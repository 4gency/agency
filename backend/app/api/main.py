from fastapi import APIRouter

from app.api.routes import configs, login, subscription, users, utils, checkout

api_router = APIRouter()
api_router.include_router(login.router, tags=["login"])
api_router.include_router(users.router, prefix="/users", tags=["users"])
api_router.include_router(utils.router, prefix="/utils", tags=["utils"])
api_router.include_router(configs.router, prefix="/configs", tags=["configs"])
api_router.include_router(subscription.router, prefix="/subscription", tags=["subscription"]) # noqa
api_router.include_router(checkout.router, prefix="/checkout", tags=["checkout"])
