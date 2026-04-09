"""Auth0 JWT verification middleware with bypass mode for development."""

import logging
from typing import Optional

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from app.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

security = HTTPBearer(auto_error=False)

# Default dev user returned in bypass mode
DEV_USER = {
    "sub": "dev|bypass",
    "name": "Dev User",
    "email": "dev@civicpulse.local",
    "role": "coordinator",
}


def _auth0_configured() -> bool:
    """Check if Auth0 env vars are set and meaningful."""
    try:
        domain = settings.auth0_domain
        return bool(domain and "your-tenant" not in domain)
    except Exception:
        return False


async def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
) -> dict:
    """
    Verify Auth0 JWT token.
    In dev/bypass mode (no AUTH0_DOMAIN set), returns a default dev user.
    """
    if not _auth0_configured():
        logger.debug("Auth0 not configured — running in bypass mode")
        return DEV_USER

    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="No authentication credentials provided",
        )

    token = credentials.credentials
    try:
        import jwt
        from jwt import PyJWKClient

        jwks_url = f"https://{settings.auth0_domain}/.well-known/jwks.json"
        jwks_client = PyJWKClient(jwks_url)
        signing_key = jwks_client.get_signing_key_from_jwt(token)

        payload = jwt.decode(
            token,
            signing_key.key,
            algorithms=["RS256"],
            audience=settings.auth0_audience,
        )
        return payload
    except Exception as e:
        logger.warning(f"JWT verification failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
        )
