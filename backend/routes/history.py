from fastapi import APIRouter
from database.database import get_all_analyses

router = APIRouter()

@router.get("/history")
def get_history():
    """Retorna o histórico de análises realizadas."""
    return get_all_analyses()