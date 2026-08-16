from fastapi import APIRouter

router = APIRouter(prefix="/api/v1/histories", tags=["histories"])


@router.get("")
def histories(game_id: str):
    pass


@router.get("/{histories_id}")
def get_history(histories_id: str):
    pass
