import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import test from "node:test";
import vm from "node:vm";

const APP_PATH = new URL("../frontend/app.js", import.meta.url);

function makeResponse(status, body) {
  return {
    ok: status >= 200 && status < 300,
    status,
    async json() {
      return body;
    },
  };
}

function deferred() {
  let resolve;
  const promise = new Promise((done) => {
    resolve = done;
  });
  return { promise, resolve };
}

async function until(predicate) {
  for (let attempt = 0; attempt < 50; attempt += 1) {
    if (predicate()) return;
    await new Promise((resolve) => setTimeout(resolve, 0));
  }
  assert.fail("Timed out waiting for asynchronous state");
}

function loadApp(fetchImpl = async () => makeResponse(500, {})) {
  const storage = new Map();
  const sandbox = {
    AbortController,
    Blob,
    URL,
    clearTimeout,
    console,
    fetch: (...args) => fetchImpl(...args),
    localStorage: {
      getItem: (key) => storage.get(key) ?? null,
      setItem: (key, value) => storage.set(key, String(value)),
    },
    setTimeout,
    structuredClone,
    window: { addEventListener() {} },
    document: {
      addEventListener() {},
      getElementById() { return null; },
    },
  };
  sandbox.globalThis = sandbox;
  vm.createContext(sandbox);

  const source = `${readFileSync(APP_PATH, "utf8")}\n
    globalThis.__appTest = {
      apiBaseUrl: API_BASE_URL,
      areGroupsEqual,
      enqueuePersist,
      parseLocalGroups,
      processPersistQueue,
      writeLocalStorage,
      getState: () => ({
        confirmedServerVersion,
        isBackendOnline,
        isPersisting,
        pendingStateToPersist,
        syncMode,
      }),
      setSyncState: (value) => {
        confirmedServerVersion = value.version ?? 0;
        isBackendOnline = value.online ?? true;
        syncMode = value.mode ?? "synced";
        syncPreference = "auto";
      },
      captureConflictWith: (callback) => {
        handleVersionConflict = async (latestGroups) => callback(latestGroups);
      },
    };
  `;
  vm.runInContext(source, sandbox, { filename: "app.js" });
  return { api: sandbox.__appTest, storage };
}

test("uses same-origin API and localStorage survives a reload", () => {
  const { api } = loadApp();
  const groups = [{ id: "g1", balances: { B: -1, A: 1 } }];

  assert.equal(api.apiBaseUrl, "");
  assert.equal(api.writeLocalStorage(groups), true);
  assert.equal(JSON.stringify(api.parseLocalGroups()), JSON.stringify(groups));
});

test("comparison ignores object-key ordering", () => {
  const { api } = loadApp();
  const a = [{ id: "g", name: "G", members: ["A", "B"], balances: { A: 1, B: -1 }, expenses: [] }];
  const b = [{ id: "g", name: "G", members: ["B", "A"], balances: { B: -1, A: 1 }, expenses: [] }];

  assert.equal(api.areGroupsEqual(a, b), true);
});

test("serializes rapid PUTs and advances the confirmed version", async () => {
  const firstRequest = deferred();
  const calls = [];
  const { api } = loadApp(async (_url, options) => {
    calls.push(JSON.parse(options.body));
    if (calls.length === 1) return firstRequest.promise;
    return makeResponse(200, { version: 2, data: calls[1].data });
  });
  api.setSyncState({ version: 0 });

  const first = [{ id: "first" }];
  const latest = [{ id: "latest" }];
  api.enqueuePersist(first);
  api.enqueuePersist(latest);
  firstRequest.resolve(makeResponse(200, { version: 1, data: { groups: first } }));

  await until(() => calls.length === 2 && !api.getState().isPersisting);
  assert.equal(calls[0].expected_version, 0);
  assert.equal(calls[1].expected_version, 1);
  assert.deepEqual(calls[1].data.groups, latest);
  assert.equal(api.getState().confirmedServerVersion, 2);
});

test("a 409 preserves the newest mutation made while the PUT was in flight", async () => {
  const firstRequest = deferred();
  let conflictSnapshot;
  const { api } = loadApp(async () => firstRequest.promise);
  api.setSyncState({ version: 3 });
  api.captureConflictWith((groups) => {
    conflictSnapshot = groups;
  });

  api.enqueuePersist([{ id: "sent" }]);
  api.enqueuePersist([{ id: "newest" }]);
  firstRequest.resolve(makeResponse(409, { detail: { current_version: 4 } }));

  await until(() => Boolean(conflictSnapshot));
  assert.deepEqual(conflictSnapshot, [{ id: "newest" }]);
  assert.equal(api.getState().pendingStateToPersist, null);
  assert.equal(api.getState().syncMode, "conflict");
});

test("network failure retains the snapshot and the next mutation retries", async () => {
  let shouldFail = true;
  const calls = [];
  const { api } = loadApp(async (_url, options) => {
    calls.push(JSON.parse(options.body));
    if (shouldFail) throw new Error("offline");
    return makeResponse(200, { version: 1, data: calls.at(-1).data });
  });
  api.setSyncState({ version: 0 });

  api.enqueuePersist([{ id: "offline" }]);
  await until(() => api.getState().syncMode === "error");
  assert.deepEqual(api.getState().pendingStateToPersist, [{ id: "offline" }]);

  shouldFail = false;
  api.enqueuePersist([{ id: "newest" }]);
  await until(() => api.getState().syncMode === "synced");
  assert.deepEqual(calls.at(-1).data.groups, [{ id: "newest" }]);
  assert.equal(api.getState().pendingStateToPersist, null);
});
