from fastapi import APIRouter, Depends
from services.report_service import get_report_service
from configuration.database import get_db
router = APIRouter()

@router.get("/report/{run_name}")
def get_report(run_name: str, db=Depends(get_db)):
    return get_report_service(run_name, db=db)

