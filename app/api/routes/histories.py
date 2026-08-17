from typing import Annotated

from fastapi import APIRouter, HTTPException, Query

from app.models import History, HistoryList
from app.services.histories import find_history, list_histories

router = APIRouter(prefix="/api/v1/histories", tags=["histories"])


@router.get("", response_model=HistoryList)
def histories(
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> HistoryList:
    return list_histories(limit, offset)


@router.get("/{histories_id}", response_model=History)
def get_history(histories_id: str) -> History:
    history = find_history(histories_id)
    if history is None:
        raise HTTPException(status_code=404, detail="History not found")
    return history
