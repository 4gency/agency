from fastapi import APIRouter

from app.api.routes import (
    actions,
    applies,
    bots,
    checkout,
    configs,
    credentials,
    events,
    login,
    monitoring,
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

# Novas rotas para os serviços de bot
api_router.include_router(bots.router, prefix="/bots", tags=["bots"])
api_router.include_router(
    credentials.router, prefix="/credentials", tags=["credentials"]
)
api_router.include_router(actions.router, prefix="/bots", tags=["actions"])
api_router.include_router(events.router, prefix="/bots", tags=["events"])
api_router.include_router(applies.router, prefix="/bots", tags=["applies"])
api_router.include_router(monitoring.router, prefix="/monitoring", tags=["monitoring"])
