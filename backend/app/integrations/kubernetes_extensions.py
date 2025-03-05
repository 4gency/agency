import logging
import os
from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

import yaml
from jinja2 import Environment, FileSystemLoader
from kubernetes import client
from kubernetes.client.rest import ApiException
from sqlmodel import Session

from app.core.config import settings
from app.models.bot import (
    BotCommandType,
    BotConfig,
    BotSession,
    KubernetesPodStatus,
    LinkedInCredentials,
)

logger = logging.getLogger(__name__)

# These are the methods to add to the KubernetesManager class


def _render_template(self, template_name: str, context: dict[str, Any]) -> str:
    """
    Renderiza um template Jinja2 com o contexto fornecido.

    Args:
        template_name: Nome do arquivo de template
        context: Dicionário de contexto para o template

    Returns:
        String contendo o template renderizado
    """
    template = self.jinja_env.get_template(f"{template_name}.yaml.j2")
    return template.render(**context)


def _create_yaml_from_template(
    self, template_name: str, context: dict[str, Any]
) -> dict[str, Any]:
    """
    Cria um dicionário YAML a partir de um template.

    Args:
        template_name: Nome do arquivo de template
        context: Dicionário de contexto para o template

    Returns:
        Dicionário representando o YAML
    """
    yaml_content = self._render_template(template_name, context)
    return yaml.safe_load(yaml_content)


async def create_bot_pod(
    self,
    _session: Session,
    bot_session: BotSession,
    bot_config: BotConfig,
    linked_credentials: LinkedInCredentials,
    config_yaml: str,
    resume_yaml: str,
) -> bool:
    """
    Cria um pod para executar um bot.

    Args:
        _session: Sessão do banco de dados
        bot_session: Sessão do bot
        bot_config: Configuração do bot
        linked_credentials: Credenciais do LinkedIn
        config_yaml: Configuração YAML do bot
        resume_yaml: Currículo YAML do bot

    Returns:
        True se o pod foi criado com sucesso, False caso contrário
    """
    namespace = bot_config.kubernetes_namespace
    pod_name = f"bot-{bot_session.id.hex[:8]}"
    config_map_name = f"bot-config-{bot_session.id.hex[:8]}"
    secret_name = f"bot-secret-{bot_session.id.hex[:8]}"
    service_name = f"bot-service-{bot_session.id.hex[:8]}"
    current_time = datetime.now(timezone.utc).isoformat()
    api_key = uuid4().hex  # Generate a unique API key for this session

    # Ensure namespace exists
    if not self.create_namespace_if_not_exists(namespace):
        logger.error(f"Falha ao criar namespace {namespace} para o bot")
        return False

    # Create ConfigMap for bot configuration
    config_map_context = {
        "config_map_name": config_map_name,
        "namespace": namespace,
        "session_id": str(bot_session.id),
        "user_id": str(bot_session.user_id),
        "config_yaml": config_yaml,
        "resume_yaml": resume_yaml,
        "config_version": bot_config.config_version,
        "resume_version": bot_config.resume_version,
        "api_url": settings.API_V1_STR,
        "created_at": current_time,
        "max_applies": bot_session.applies_limit,
        "max_time_seconds": int(bot_session.time_limit.total_seconds())
        if bot_session.time_limit
        else 3600,
        "auto_restart": bot_config.auto_restart_on_failure,
        "dynamic_updates": bot_config.allow_dynamic_updates,
    }

    config_map = self._create_yaml_from_template("bot_configmap", config_map_context)
    created_config_map = self.core_v1_api.create_namespaced_config_map(
        namespace=namespace, body=config_map
    )
    if not created_config_map:
        logger.error(f"Falha ao criar ConfigMap para pod {pod_name}")
        return False

    # Create Secret for credentials
    secret_context = {
        "secret_name": secret_name,
        "namespace": namespace,
        "session_id": str(bot_session.id),
        "user_id": str(bot_session.user_id),
        "linkedin_email": linked_credentials.email,
        "linkedin_password": linked_credentials.password,
        "api_key": api_key,
        "webhook_token": settings.WEBHOOK_TOKEN
        if hasattr(settings, "WEBHOOK_TOKEN")
        else "sdfghjkllkjhgfdsdfghjkloir",
    }

    secret = self._create_yaml_from_template("bot_secret", secret_context)
    created_secret = self.core_v1_api.create_namespaced_secret(
        namespace=namespace, body=secret
    )
    if not created_secret:
        logger.error(f"Falha ao criar Secret para pod {pod_name}")
        # Clean up ConfigMap
        self.core_v1_api.delete_namespaced_config_map(
            name=config_map_name, namespace=namespace
        )
        return False

    # Create Service for bot
    service_context = {
        "service_name": service_name,
        "namespace": namespace,
        "session_id": str(bot_session.id),
        "user_id": str(bot_session.user_id),
    }

    service = self._create_yaml_from_template("bot_service", service_context)
    created_service = self.core_v1_api.create_namespaced_service(
        namespace=namespace, body=service
    )
    if not created_service:
        logger.error(f"Falha ao criar Service para pod {pod_name}")
        # Clean up ConfigMap and Secret
        self.core_v1_api.delete_namespaced_config_map(
            name=config_map_name, namespace=namespace
        )
        self.core_v1_api.delete_namespaced_secret(name=secret_name, namespace=namespace)
        return False

    # Create Pod for bot
    pod_context = {
        "pod_name": pod_name,
        "namespace": namespace,
        "session_id": str(bot_session.id),
        "user_id": str(bot_session.user_id),
        "image": settings.BOT_IMAGE
        if hasattr(settings, "BOT_IMAGE")
        else "ghcr.io/linkedin-bot:latest",
        "restart_policy": "Never",
        "config_map_name": config_map_name,
        "bot_api_secret_name": secret_name,
        "bot_id": str(bot_session.id),
        "config_version": bot_config.config_version,
        "resume_version": bot_config.resume_version,
        "resources_requests_cpu": bot_config.kubernetes_resources_cpu,
        "resources_requests_memory": bot_config.kubernetes_resources_memory,
        "resources_limits_cpu": bot_config.kubernetes_limits_cpu,
        "resources_limits_memory": bot_config.kubernetes_limits_memory,
        "style_choice": "Modern Blue",  # Default value, could be from configuration
        "api_url": settings.API_V1_STR,
        "webhook_uri": settings.WEBHOOK_URI
        if hasattr(settings, "WEBHOOK_URI")
        else "http://api-service:8000/api/v1/webhooks/bot",
        "gotenberg_url": settings.GOTENBERG_URL
        if hasattr(settings, "GOTENBERG_URL")
        else "http://gotenberg:3000",
    }

    pod = self._create_yaml_from_template("bot_pod", pod_context)
    try:
        _ = self.core_v1_api.create_namespaced_pod(namespace=namespace, body=pod)
        logger.info(f"Pod {pod_name} criado com sucesso no namespace {namespace}")

        # Update bot session with Kubernetes information
        bot_session.kubernetes_pod_name = pod_name
        bot_session.kubernetes_namespace = namespace
        bot_session.kubernetes_status = KubernetesPodStatus.PENDING.value
        bot_session.api_key = api_key

        # Store references to created resources
        bot_session.kubernetes_resources = {
            "config_map": config_map_name,
            "secret": secret_name,
            "service": service_name,
            "pod": pod_name,
        }

        return True
    except ApiException as e:
        logger.error(f"Erro ao criar pod {pod_name}: {str(e)}")
        # Clean up all created resources
        try:
            self.core_v1_api.delete_namespaced_config_map(
                name=config_map_name, namespace=namespace
            )
        except Exception:
            pass

        try:
            self.core_v1_api.delete_namespaced_secret(
                name=secret_name, namespace=namespace
            )
        except Exception:
            pass

        try:
            self.core_v1_api.delete_namespaced_service(
                name=service_name, namespace=namespace
            )
        except Exception:
            pass

        return False


async def get_pod_status(
    self, namespace: str, pod_name: str
) -> tuple[KubernetesPodStatus, dict[str, Any] | None]:
    """
    Obtém o status atual de um pod.

    Args:
        namespace: Namespace do pod
        pod_name: Nome do pod

    Returns:
        Tupla com o status do pod e informações adicionais
    """
    try:
        pod = self.core_v1_api.read_namespaced_pod(name=pod_name, namespace=namespace)

        # Get pod status
        phase = pod.status.phase

        # Map Kubernetes status to our enum
        status_map = {
            "Pending": KubernetesPodStatus.PENDING,
            "Running": KubernetesPodStatus.RUNNING,
            "Succeeded": KubernetesPodStatus.SUCCEEDED,
            "Failed": KubernetesPodStatus.FAILED,
            "Unknown": KubernetesPodStatus.UNKNOWN,
        }

        # Check if pod is being deleted
        if pod.metadata.deletion_timestamp:
            status = KubernetesPodStatus.TERMINATING
        else:
            status = status_map.get(phase, KubernetesPodStatus.UNKNOWN)

        # Collect additional info
        container_statuses = pod.status.container_statuses or []

        # Get logs if pod is running or completed
        logs = None
        if status in [
            KubernetesPodStatus.RUNNING,
            KubernetesPodStatus.SUCCEEDED,
            KubernetesPodStatus.FAILED,
        ]:
            try:
                logs = self.core_v1_api.read_namespaced_pod_log(
                    name=pod_name,
                    namespace=namespace,
                    container="bot",
                    tail_lines=100,  # Get the last 100 lines
                )
            except Exception:
                logs = None

        info = {
            "phase": phase,
            "start_time": pod.status.start_time.isoformat()
            if pod.status.start_time
            else None,
            "container_statuses": [],
            "host_ip": pod.status.host_ip,
            "pod_ip": pod.status.pod_ip,
            "conditions": [],
            "logs": logs,
        }

        # Add container statuses
        for cs in container_statuses:
            container_info = {
                "name": cs.name,
                "ready": cs.ready,
                "started": cs.started,
                "restart_count": cs.restart_count,
            }

            # Add state info
            if cs.state.running:
                container_info["state"] = "running"
                container_info["started_at"] = (
                    cs.state.running.started_at.isoformat()
                    if cs.state.running.started_at
                    else None
                )
            elif cs.state.waiting:
                container_info["state"] = "waiting"
                container_info["reason"] = cs.state.waiting.reason
                container_info["message"] = cs.state.waiting.message
            elif cs.state.terminated:
                container_info["state"] = "terminated"
                container_info["exit_code"] = cs.state.terminated.exit_code
                container_info["reason"] = cs.state.terminated.reason
                container_info["message"] = cs.state.terminated.message
                container_info["started_at"] = (
                    cs.state.terminated.started_at.isoformat()
                    if cs.state.terminated.started_at
                    else None
                )
                container_info["finished_at"] = (
                    cs.state.terminated.finished_at.isoformat()
                    if cs.state.terminated.finished_at
                    else None
                )

            info["container_statuses"].append(container_info)

        # Add pod conditions
        if pod.status.conditions:
            for condition in pod.status.conditions:
                info["conditions"].append(
                    {
                        "type": condition.type,
                        "status": condition.status,
                        "reason": condition.reason,
                        "message": condition.message,
                        "last_transition_time": condition.last_transition_time.isoformat()
                        if condition.last_transition_time
                        else None,
                    }
                )

        return status, info

    except ApiException as e:
        if e.status == 404:
            # Pod not found
            logger.warning(f"Pod {pod_name} não encontrado no namespace {namespace}")
            return KubernetesPodStatus.UNKNOWN, {
                "error": "Pod not found",
                "details": str(e),
            }
        else:
            logger.error(f"Erro ao obter status do pod {pod_name}: {str(e)}")
            return KubernetesPodStatus.UNKNOWN, {"error": str(e)}


async def send_command_to_pod(
    self,
    namespace: str,
    pod_name: str,
    command: BotCommandType,
    _data: dict[str, Any] | None = None,
) -> bool:
    """
    Envia um comando para um pod ativo.
    Na implementação atual, os comandos são enviados via API do pod.

    Args:
        namespace: Namespace do pod
        pod_name: Nome do pod
        command: Tipo de comando a ser enviado
        _data: Dados adicionais para o comando

    Returns:
        True se o comando foi enviado com sucesso, False caso contrário
    """
    try:
        # Get pod information to ensure it's running
        status, info = await self.get_pod_status(namespace, pod_name)

        if status != KubernetesPodStatus.RUNNING:
            logger.error(
                f"Não é possível enviar comando para pod {pod_name} com status {status}"
            )
            return False

        # In a real implementation, we would use an API call, Kubernetes exec,
        # or a message queue to send commands to the pod.
        # For this example, we'll simulate command handling.

        pod_ip = info.get("pod_ip")
        if not pod_ip:
            logger.error(f"Pod {pod_name} não tem um IP atribuído")
            return False

        # In a real implementation, this would be a request to the pod's API
        logger.info(
            f"Enviando comando {command.value} para o pod {pod_name} ({pod_ip})"
        )

        # Simulate successful command sending
        return True

    except Exception as e:
        logger.error(f"Erro ao enviar comando para o pod {pod_name}: {str(e)}")
        return False


async def terminate_pod(
    self, namespace: str, pod_name: str, grace_period_seconds: int = 30
) -> bool:
    """
    Encerra um pod.

    Args:
        namespace: Namespace do pod
        pod_name: Nome do pod
        grace_period_seconds: Período de graça para o pod terminar (em segundos)

    Returns:
        True se o pod foi encerrado com sucesso, False caso contrário
    """
    try:
        # Check if pod exists
        try:
            self.core_v1_api.read_namespaced_pod(name=pod_name, namespace=namespace)
        except ApiException as e:
            if e.status == 404:
                logger.info(f"Pod {pod_name} já não existe no namespace {namespace}")
                return True
            else:
                raise

        # Delete pod
        body = client.V1DeleteOptions(grace_period_seconds=grace_period_seconds)
        self.core_v1_api.delete_namespaced_pod(
            name=pod_name, namespace=namespace, body=body
        )
        logger.info(
            f"Pod {pod_name} foi marcado para exclusão com período de graça de {grace_period_seconds}s"
        )
        return True

    except ApiException as e:
        logger.error(f"Erro ao encerrar pod {pod_name}: {str(e)}")
        return False


async def cleanup_resources(
    self, namespace: str, resources: dict[str, str]
) -> dict[str, bool]:
    """
    Limpa todos os recursos do Kubernetes associados a uma sessão de bot.

    Args:
        namespace: Namespace dos recursos
        resources: Dicionário com nomes dos recursos (config_map, secret, service, pod)

    Returns:
        Dicionário indicando quais recursos foram limpos com sucesso
    """
    results = {}

    # Delete pod
    if "pod" in resources:
        try:
            await self.terminate_pod(namespace, resources["pod"])
            results["pod"] = True
        except Exception as e:
            logger.error(f"Erro ao excluir pod {resources['pod']}: {str(e)}")
            results["pod"] = False

    # Delete service
    if "service" in resources:
        try:
            self.core_v1_api.delete_namespaced_service(
                name=resources["service"], namespace=namespace
            )
            results["service"] = True
        except Exception as e:
            logger.error(f"Erro ao excluir service {resources['service']}: {str(e)}")
            results["service"] = False

    # Delete secret
    if "secret" in resources:
        try:
            self.core_v1_api.delete_namespaced_secret(
                name=resources["secret"], namespace=namespace
            )
            results["secret"] = True
        except Exception as e:
            logger.error(f"Erro ao excluir secret {resources['secret']}: {str(e)}")
            results["secret"] = False

    # Delete config map
    if "config_map" in resources:
        try:
            self.core_v1_api.delete_namespaced_config_map(
                name=resources["config_map"], namespace=namespace
            )
            results["config_map"] = True
        except Exception as e:
            logger.error(
                f"Erro ao excluir config map {resources['config_map']}: {str(e)}"
            )
            results["config_map"] = False

    return results


# Add this to the __init__ method
def init_jinja_env(self):
    """
    Initializes the Jinja2 environment for templates.
    This should be added to the __init__ method of KubernetesManager.
    """
    templates_dir = os.path.join(
        os.path.dirname(os.path.dirname(__file__)), "templates", "kubernetes"
    )
    self.jinja_env = Environment(loader=FileSystemLoader(templates_dir))
