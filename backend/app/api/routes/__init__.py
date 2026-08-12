from fastapi import APIRouter

from app.api.routes import analyze, dashboard, graph, processes, roles_skills

api_router = APIRouter()
api_router.include_router(dashboard.router)
api_router.include_router(processes.router)
api_router.include_router(roles_skills.router)
api_router.include_router(graph.router)
api_router.include_router(analyze.router)
