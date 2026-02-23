from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import jwt, JWTError
from pydantic import ValidationError
from backend.app.core.config import settings
from typing import Optional, Dict, Any

# OAuth2 scheme that points to Keycloak token endpoint (just for swagger UI info)
oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl=f"{settings.KEYCLOAK_URL}/realms/{settings.KEYCLOAK_REALM}/protocol/openid-connect/token",
    auto_error=False
)

async def get_current_user(token: Optional[str] = Depends(oauth2_scheme)) -> Dict[str, Any]:
    # Placeholder user for no-auth mode
    print("DEBUG: Bypassing authentication, returning Admin User")
    return {
        "sub": "00000000-0000-0000-0000-000000000000",
        "preferred_username": "admin",
        "email": "admin@example.com",
        "name": "Admin User"
    }

async def get_current_active_user(current_user: Dict[str, Any] = Depends(get_current_user)) -> Dict[str, Any]:
    return current_user
