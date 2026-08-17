import asyncio
from collections.abc import Awaitable, Callable
from typing import TypeVar

from pydantic import BaseModel

from app.models import History, HistoryList, HistoryMethod
from app.repositories import histories as history_repository

ResponseModel = TypeVar("ResponseModel", bound=BaseModel)


async def execute_with_history(
    method: HistoryMethod,
    request: BaseModel,
    operation: Callable[[], Awaitable[ResponseModel]],) -> ResponseModel:

    history_id = await asyncio.to_thread(
        history_repository.create,
        method,
        request.model_dump(mode="json"),
    )
    try:
        response = await operation()
    except Exception as exc:
        await asyncio.to_thread(
            history_repository.finish,
            history_id,
            error=str(exc) or exc.__class__.__name__,
        )
        raise
    await asyncio.to_thread(
        history_repository.finish,
        history_id,
        result=response.model_dump(mode="json"),
    )
    return response


def list_histories(limit: int, offset: int) -> HistoryList:
    return history_repository.list_all(limit, offset)


def find_history(history_id: str) -> History | None:
    return history_repository.find(history_id)
