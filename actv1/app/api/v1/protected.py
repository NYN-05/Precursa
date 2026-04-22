from fastapi import APIRouter, Depends

from app.api.deps import AuthContext, require_roles

router = APIRouter(prefix="/protected", tags=["protected"])


@router.get("/admin")
async def admin_only(
    context: AuthContext = Depends(require_roles("admin")),
) -> dict[str, str]:
    return {
        "message": f"Admin access granted to {context['username']}",
        "role_check": "passed",
    }


@router.get("/ops")
async def ops_access(
    context: AuthContext = Depends(
        require_roles("admin", "ops_analyst", "logistics_manager")
    ),
) -> dict[str, str]:
    return {
        "message": f"Operations access granted to {context['username']}",
        "role_check": "passed",
    }
