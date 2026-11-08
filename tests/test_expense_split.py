
import sys
from pathlib import Path

# Cho phép Python tìm module trong thư mục src
PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from expense_split import calculate_equal_split


# Test 1: Chia đều 500003 VND cho 3 thành viên
total_amount = 500003
members = ["An", "Binh", "Chi"]
leader_index = 0

shares = calculate_equal_split(
    total_amount,
    members,
    leader_index
)

print("Allocation:", shares)
print("Total allocated:", sum(shares))

assert shares == [166669, 166667, 166667]
assert sum(shares) == total_amount

print("PASS: Equal Split test")

# Test 2: Chia hết, không có phần dư
shares = calculate_equal_split(
    600000,
    ["An", "Binh", "Chi"],
    0
)

assert shares == [200000, 200000, 200000]
assert sum(shares) == 600000

print("PASS: Equal Split without remainder")


# Test 3: Nhóm chỉ có một thành viên
shares = calculate_equal_split(
    100000,
    ["An"],
    0
)

assert shares == [100000]
assert sum(shares) == 100000

print("PASS: Equal Split with one member")


# Test 4: Nhóm không có thành viên
try:
    calculate_equal_split(100000, [], 0)
except ValueError:
    print("PASS: Empty group validation")
else:
    raise AssertionError("Empty group should raise ValueError")


# Test 5: Leader index không hợp lệ
try:
    calculate_equal_split(100000, ["An", "Binh"], 2)
except ValueError:
    print("PASS: Invalid leader validation")
else:
    raise AssertionError("Invalid leader should raise ValueError")

from expense_split import calculate_percentage_split


# Test 6: Percentage Split với phần dư
total_amount = 500003
members = ["An", "Binh", "Chi"]
percentages = [40, 35, 25]
leader_index = 0

shares = calculate_percentage_split(
    total_amount,
    members,
    percentages,
    leader_index
)

print("Percentage allocation:", shares)
print("Total allocated:", sum(shares))

assert shares == [200002, 175001, 125000]
assert sum(shares) == total_amount

print("PASS: Percentage Split with remainder")


# Test 7: Percentage Split không có phần dư
shares = calculate_percentage_split(
    600000,
    ["An", "Binh", "Chi"],
    [40, 35, 25],
    0
)

assert shares == [240000, 210000, 150000]
assert sum(shares) == 600000

print("PASS: Percentage Split without remainder")


# Test 8: Tổng tỷ lệ không bằng 100%
try:
    calculate_percentage_split(
        500000,
        ["An", "Binh", "Chi"],
        [40, 30, 20],
        0
    )
except ValueError:
    print("PASS: Invalid percentage validation")
else:
    raise AssertionError("Invalid percentages should raise ValueError")


# Test 9: Số thành viên và số tỷ lệ không khớp
try:
    calculate_percentage_split(
        500000,
        ["An", "Binh", "Chi"],
        [50, 50],
        0
    )
except ValueError:
    print("PASS: Member and percentage count validation")
else:
    raise AssertionError("Mismatched lists should raise ValueError")

from expense_split import calculate_fixed_split


# Test 10: Fixed Split hợp lệ
shares = calculate_fixed_split(
    500000,
    ["An", "Binh", "Chi"],
    [100000, 150000, 250000]
)

print("Fixed allocation:", shares)
print("Total allocated:", sum(shares))

assert shares == [100000, 150000, 250000]
assert sum(shares) == 500000

print("PASS: Fixed Split")


# Test 11: Tổng tiền phân bổ không bằng hóa đơn
try:
    calculate_fixed_split(
        500000,
        ["An", "Binh", "Chi"],
        [100000, 150000, 200000]
    )
except ValueError:
    print("PASS: Fixed amount total validation")
else:
    raise AssertionError("Incorrect total should raise ValueError")


# Test 12: Số thành viên và số tiền không khớp
try:
    calculate_fixed_split(
        500000,
        ["An", "Binh", "Chi"],
        [250000, 250000]
    )
except ValueError:
    print("PASS: Fixed member count validation")
else:
    raise AssertionError("Mismatched lists should raise ValueError")


# Test 13: Số tiền âm
try:
    calculate_fixed_split(
        500000,
        ["An", "Binh"],
        [600000, -100000]
    )
except ValueError:
    print("PASS: Negative fixed amount validation")
else:
    raise AssertionError("Negative amount should raise ValueError")


# Test 14: Số tiền dạng float
try:
    calculate_fixed_split(
        500000,
        ["An", "Binh"],
        [250000.5, 249999.5]
    )
except ValueError:
    print("PASS: Integer VND validation")
else:
    raise AssertionError("Float amount should raise ValueError")
