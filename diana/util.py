import asyncio
import inspect


def isasync(func):
    wrapped = getattr(func, "__wrapped__", None)
    return (
        asyncio.iscoroutinefunction(func)
        or inspect.isasyncgenfunction(func)
        or asyncio.iscoroutinefunction(wrapped)
        or inspect.isasyncgenfunction(wrapped)
        or hasattr(func, "__aenter__")
    )
