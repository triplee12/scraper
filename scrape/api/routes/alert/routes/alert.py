from typing import List
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status, Query
from scrape.core.logger import logger
from scrape.db.database import get_repository
from scrape.db.repositories.alert.alert import AlertRepository
from scrape.models.users.user import UserInDB
from scrape.services.auth.auth_service import get_current_user

router = APIRouter()


@router.post("/set", response_model=UUID)
async def create_alert(
    product_id: UUID = Query(...),
    target_price: float = Query(...),
    repo: AlertRepository = Depends(get_repository(AlertRepository)),
    current_user: UserInDB = Depends(get_current_user),
) -> UUID:
    try:
        logger.info("Creating alert")
        alert = {
            "user_id": current_user.id,
            "product_id": product_id,
            "target_price": target_price,
            "is_triggered": False
        }
        alert_id = await repo.create_alert(alert=alert)
        
        if not alert_id:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
                detail="Error creating alert"
            )
        return alert_id
    except Exception as e:
        logger.exception("Error creating alert. Exception: %s", e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error creating alert"
        ) from e


@router.get("/", response_model=List[UUID])
async def get_alerts(
    limit: int = Query(10, ge=0),
    repo: AlertRepository = Depends(get_repository(AlertRepository)),
    current_user: UserInDB = Depends(get_current_user),
) -> List[UUID]:
    try:
        logger.info("Getting alerts")
        alerts = await repo.get_alerts(user_id=current_user.id, limit=limit)
        return alerts
    except Exception as e:
        logger.exception("Error getting alerts. Exception: %s", e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error getting alerts"
        ) from e


@router.delete("/{alert_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_alert(
    alert_id: UUID = Query(...),
    repo: AlertRepository = Depends(get_repository(AlertRepository)),
    current_user: UserInDB = Depends(get_current_user),
):
    try:
        logger.info("Deleting alerts")
        deleted = await repo.delete_alert_by_id(
            alert_id=alert_id, user_id=current_user.id
        )

        if not deleted:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Alert not found"
            )
        return
    except Exception as e:
        logger.exception("Error deleting alerts. Exception: %s", e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error deleting alerts"
        ) from e
