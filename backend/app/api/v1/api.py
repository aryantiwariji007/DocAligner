from fastapi import APIRouter
from backend.app.api.v1.endpoints import folders, documents, standards, validation, assignments, audit, decision_flow

api_router = APIRouter()
api_router.include_router(folders.router, prefix="/folders", tags=["folders"])
api_router.include_router(documents.router, prefix="/documents", tags=["documents"])
api_router.include_router(standards.router, prefix="/standards", tags=["standards"])
api_router.include_router(validation.router, prefix="/validation", tags=["validation"])
api_router.include_router(assignments.router, prefix="/assignments", tags=["assignments"])
api_router.include_router(audit.router, prefix="/audit", tags=["audit"])
api_router.include_router(decision_flow.router, prefix="/decision-flow", tags=["decision-flow"])

