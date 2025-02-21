from fastapi import APIRouter

from app.api.routes import (
    checkout,
    configs,
    login,
    payments,
    subscription_plans,
    users,
    utils,
)

api_router = APIRouter()
api_router.include_router(login.router, tags=["login"])
api_router.include_router(users.router, prefix="/users", tags=["users"])
api_router.include_router(utils.router, prefix="/utils", tags=["utils"])
api_router.include_router(payments.router, prefix="/payments", tags=["payments"])
api_router.include_router(configs.router, prefix="/configs", tags=["configs"])
api_router.include_router(
    subscription_plans.router, prefix="/subscription-plans", tags=["subscription-plans"]
)  # noqa
api_router.include_router(checkout.router, prefix="/checkout", tags=["checkout"])
