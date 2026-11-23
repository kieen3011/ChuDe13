from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy import func, update
from . import models
from . import schemas
from .database import get_db

router = APIRouter(
    prefix="/api/demo",
    tags=["Demo State (Chủ Đề 13)"]
)

@router.get("/state", response_model=schemas.DemoStateResponse)
def get_demo_state(db: Session = Depends(get_db)):
    """
    Lấy trạng thái ứng dụng demo (bản ghi id=1).
    Nếu chưa có bản ghi trong bảng demo_state, trả về trạng thái rỗng chuẩn:
    {"id": 1, "version": 0, "data": {"groups": []}, "updated_at": null}
    Không tự động tạo hoặc ghi đè bản ghi khi chỉ gọi GET.
    """
    try:
        state = db.query(models.DemoState).filter(models.DemoState.id == 1).first()
        if not state:
            return schemas.DemoStateResponse(
                id=1,
                version=0,
                data=schemas.DemoStateData(groups=[]),
                updated_at=None
            )
        return state
    except SQLAlchemyError:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Lỗi hệ thống khi truy vấn trạng thái demo."
        )
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Đã xảy ra lỗi không xác định."
        )

@router.put("/state", response_model=schemas.DemoStateResponse)
def update_demo_state(payload: schemas.DemoStatePayload, db: Session = Depends(get_db)):
    """
    Cập nhật / Lưu toàn bộ trạng thái demo ứng dụng dưới dạng JSONB có kiểm soát phiên bản (OCC).
    Sử dụng upsert có điều kiện nguyên tử PostgreSQL:
    ON CONFLICT (id) DO UPDATE ... WHERE demo_state.version = expected_version
    Nếu expected_version không khớp hoặc bản ghi đã bị thay đổi bởi client khác -> trả về HTTP 409 Conflict.
    """
    try:
        data_dict = payload.data.model_dump(mode="json")
        expected_ver = payload.expected_version

        # Trường hợp 1: Client mong đợi tạo bản ghi ban đầu (expected_version == 0)
        if expected_ver == 0:
            persisted = models.DemoState(
                id=1,
                version=1,
                data=data_dict,
                updated_at=func.now(),
            )
            db.add(persisted)
            try:
                db.commit()
            except IntegrityError:
                # The primary-key constraint arbitrates concurrent initial
                # writes atomically. The losing client receives a 409.
                db.rollback()
                current_state = db.query(models.DemoState).filter(models.DemoState.id == 1).first()
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail={
                        "code": "VERSION_CONFLICT",
                        "message": "Dữ liệu đã được tạo bởi một thiết bị khác trong lúc gửi.",
                        "current_version": current_state.version if current_state else 0,
                    },
                )
            db.refresh(persisted)
            return persisted

        # Trường hợp 2: Cập nhật bản ghi đang tồn tại (expected_version > 0)
        stmt = (
            update(models.DemoState)
            .where(
                models.DemoState.id == 1,
                models.DemoState.version == expected_ver,
            )
            .values(
                version=models.DemoState.version + 1,
                data=data_dict,
                updated_at=func.now(),
            )
            .returning(models.DemoState)
        )

        result = db.execute(stmt)
        persisted = result.scalar_one_or_none()

        if not persisted:
            # Không cập nhật được dòng nào -> Xung đột phiên bản (OCC Conflict)
            db.rollback()
            current_state = db.query(models.DemoState).filter(models.DemoState.id == 1).first()
            current_ver = current_state.version if current_state else 0
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail={
                    "code": "VERSION_CONFLICT",
                    "message": "Dữ liệu đã được cập nhật bởi một thiết bị khác.",
                    "current_version": current_ver
                }
            )

        db.commit()
        return persisted

    except HTTPException:
        # Giữ nguyên HTTPException (409, 422, etc.)
        raise
    except SQLAlchemyError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Lỗi hệ thống khi lưu trữ trạng thái demo."
        )
    except Exception:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Đã xảy ra lỗi không xác định khi lưu trạng thái."
        )
