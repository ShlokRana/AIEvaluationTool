from fastapi import APIRouter, Depends, HTTPException

from schemas import AllFiltersResponse
from services.filters import get_all_filters_service
from configuration.database import get_db

router = APIRouter()

@router.get(
    "/get_all_filters",
    response_model=AllFiltersResponse
)
def get_all_filters(db = Depends(get_db)):
    try:
        return get_all_filters_service(db)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))