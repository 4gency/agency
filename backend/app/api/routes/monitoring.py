from typing import Any
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status

from app.api.deps import SessionDep, get_current_active_superuser
from app.models.bot import BotSession, KubernetesPodStatus
from app.models.core import ErrorMessage, Message
from app.services.monitoring import MonitoringService

router = APIRouter()


@router.get(
    "/sessions",
    dependencies=[Depends(get_current_active_superuser)],
    responses={
        401: {"model": ErrorMessage, "description": "Authentication error"},
        403: {"model": ErrorMessage, "description": "Permission error"},
    },
)
def get_all_active_sessions(
    *,
    session: SessionDep,
) -> Any:
    """
    Get all active bot sessions (admin only).
    """
    monitoring_service = MonitoringService(session)
    stalled_sessions = monitoring_service.check_stalled_sessions()
    zombie_sessions = monitoring_service.check_zombie_sessions()

    all_sessions = stalled_sessions + zombie_sessions

    return {"total": len(all_sessions), "items": all_sessions}


@router.get(
    "/sessions/status",
    dependencies=[Depends(get_current_active_superuser)],
    responses={
        401: {"model": ErrorMessage, "description": "Authentication error"},
        403: {"model": ErrorMessage, "description": "Permission error"},
    },
)
def get_sessions_status_summary(
    *,
    session: SessionDep,
) -> Any:
    """
    Get sessions status summary (admin only).
    """
    monitoring_service = MonitoringService(session)
    summary = monitoring_service.get_system_health()

    return summary


@router.get(
    "/kubernetes/pods",
    dependencies=[Depends(get_current_active_superuser)],
    responses={
        401: {"model": ErrorMessage, "description": "Authentication error"},
        403: {"model": ErrorMessage, "description": "Permission error"},
    },
)
def get_kubernetes_pods(
    *,
    session: SessionDep,
) -> Any:
    """
    Get Kubernetes pods status (admin only).
    """
    monitoring_service = MonitoringService(session)
    stalled_sessions = monitoring_service.check_stalled_sessions()
    zombie_sessions = monitoring_service.check_zombie_sessions()

    pods_info: list[dict[str, Any]] = []
    for s in stalled_sessions + zombie_sessions:
        session_data: BotSession = s
        pod_info = {
            "session_id": str(session_data.id),
            "kubernetes_pod_name": session_data.kubernetes_pod_name,
            "kubernetes_namespace": session_data.kubernetes_namespace,
            "kubernetes_pod_status": session_data.kubernetes_pod_status.value
            if session_data.kubernetes_pod_status
            else "unknown",
            "kubernetes_pod_ip": session_data.kubernetes_pod_ip,
        }
        pods_info.append(pod_info)

    return pods_info


@router.post(
    "/sessions/{session_id}/force-stop",
    dependencies=[Depends(get_current_active_superuser)],
    response_model=Message,
    responses={
        401: {"model": ErrorMessage, "description": "Authentication error"},
        403: {"model": ErrorMessage, "description": "Permission error"},
        404: {"model": ErrorMessage, "description": "Bot session not found"},
    },
)
def force_stop_session(*, session: SessionDep, session_id: UUID) -> Any:
    """
    Force stop a bot session (admin only).
    """
    monitoring_service = MonitoringService(session)

    try:
        result = monitoring_service.update_session_pod_status(
            session_id=session_id, pod_status=KubernetesPodStatus.FAILED
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error stopping session: {str(e)}",
        )

    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Bot session not found or could not be stopped",
        )

    return {"message": "Bot session force stopped successfully"}
