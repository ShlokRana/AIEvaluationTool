import subprocess
import os
import sys
from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import JSONResponse
from database.fastapi_deps import _get_db
from lib.orm.DB import DB

importer_router = APIRouter(prefix="/api/importer")


@importer_router.post("/run", summary="Run data importer", tags=["Importer"])
async def run_importer(db: DB = Depends(_get_db)):
    """
    Runs the importer script to import data into the database.
    This endpoint triggers the importer/main.py script.
    """
    try:
        # Path to the importer script
        importer_path = os.path.abspath(
            os.path.join(os.path.dirname(__file__), "../../../../importer/main.py")
        )
        
        if not os.path.exists(importer_path):
            raise HTTPException(
                status_code=404,
                detail=f"Importer script not found at {importer_path}"
            )
        
        # Get the config path
        importer_dir = os.path.dirname(importer_path)
        config_path = os.path.join(importer_dir, "config.json")
        
        # Run the importer script
        result = subprocess.run(
            [sys.executable, importer_path, "--config", config_path],
            capture_output=True,
            text=True,
            timeout=300  # 5 minute timeout
        )
        
        if result.returncode != 0:
            return JSONResponse(
                status_code=400,
                content={
                    "status": "error",
                    "message": "Importer script failed",
                    "error": result.stderr,
                    "stdout": result.stdout
                }
            )
        
        return JSONResponse(
            status_code=200,
            content={
                "status": "success",
                "message": "Data imported successfully",
                "output": result.stdout
            }
        )
        
    except subprocess.TimeoutExpired:
        raise HTTPException(
            status_code=408,
            detail="Importer script execution timed out"
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error running importer: {str(e)}"
        )
