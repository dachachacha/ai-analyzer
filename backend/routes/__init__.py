# routes/__init__.py

from .analyze import router as analyze_router
from .query import router as query_router
from .flush import router as flush_router
from .health import router as health_router
from .hashes import router as hashes_router
from .history import router as history_router

def include_routers(app):
    app.include_router(analyze_router)
    app.include_router(query_router)
    app.include_router(flush_router)
    app.include_router(health_router)
    app.include_router(hashes_router)
    app.include_router(history_router)

