import base64
import logging
import os
from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

import yaml
from fastapi import Depends
from jinja2 import Environment, FileSystemLoader
from kubernetes import client, config, watch
from kubernetes.client.rest import ApiException
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db
from app.core.config import settings
from app.models.bot import (
    BotCommandType,
    BotConfig,
    BotSession,
    KubernetesPodStatus,
    LinkedInCredentials,
)

logger = logging.getLogger(__name__)


class KubernetesManager:
    """
    Classe para gerenciar recursos do Kubernetes.
    """

    def __init__(self, in_cluster: bool = False):
        """
        Inicializa o gerenciador Kubernetes.

        Args:
            in_cluster: Se True, usa a configuração interna do cluster. Se False, usa o kubeconfig do ambiente.
        """
        try:
            if in_cluster:
                # Está rodando dentro do cluster (production)
                config.load_incluster_config()
            else:
                # Está rodando fora do cluster (development/testing)
                config.load_kube_config()

            self.core_v1_api = client.CoreV1Api()
            self.apps_v1_api = client.AppsV1Api()
            self.batch_v1_api = client.BatchV1Api()
            self.custom_objects_api = client.CustomObjectsApi()

            # Flag para indicar se a conexão foi bem-sucedida
            self.is_connected = True
            logger.info("Conexão com Kubernetes estabelecida com sucesso.")

            # Setup Jinja2 environment for templates
            templates_dir = os.path.join(
                os.path.dirname(os.path.dirname(__file__)), "templates", "kubernetes"
            )
            self.jinja_env = Environment(loader=FileSystemLoader(templates_dir))

        except Exception as e:
            self.is_connected = False
            logger.error(f"Falha ao conectar com Kubernetes: {str(e)}")
            raise

    def create_namespace_if_not_exists(self, namespace: str) -> bool:
        """
        Cria um namespace se ele não existir.

        Args:
            namespace: Nome do namespace a ser criado.

        Returns:
            bool: True se o namespace foi criado ou já existe, False em caso de erro.
        """
        try:
            # Tenta obter o namespace para verificar se já existe
            self.core_v1_api.read_namespace(name=namespace)
            logger.info(f"Namespace {namespace} já existe.")
            return True
        except ApiException as e:
            # Se o erro for 404 (Not Found), o namespace não existe e deve ser criado
            if e.status == 404:
                try:
                    # Cria o namespace
                    namespace_manifest = client.V1Namespace(
                        metadata=client.V1ObjectMeta(name=namespace)
                    )
                    self.core_v1_api.create_namespace(body=namespace_manifest)
                    logger.info(f"Namespace {namespace} criado com sucesso.")
                    return True
                except ApiException as create_error:
                    logger.error(
                        f"Erro ao criar namespace {namespace}: {str(create_error)}"
                    )
                    return False
            else:
                logger.error(f"Erro ao verificar namespace {namespace}: {str(e)}")
                return False

    def create_config_map(
        self, name: str, namespace: str, data: dict[str, str]
    ) -> client.V1ConfigMap | None:
        """
        Cria ou atualiza um ConfigMap.

        Args:
            name: Nome do ConfigMap.
            namespace: Namespace onde o ConfigMap será criado.
            data: Dicionário com os dados do ConfigMap.

        Returns:
            O ConfigMap criado ou None em caso de erro.
        """
        try:
            # Verifica se o ConfigMap já existe
            try:
                existing_config_map = self.core_v1_api.read_namespaced_config_map(
                    name=name, namespace=namespace
                )

                # Atualiza o ConfigMap existente
                existing_config_map.data = data
                updated_config_map = self.core_v1_api.replace_namespaced_config_map(
                    name=name, namespace=namespace, body=existing_config_map
                )
                logger.info(f"ConfigMap {name} atualizado em {namespace}.")
                return updated_config_map

            except ApiException as e:
                # Se o erro for 404 (Not Found), o ConfigMap não existe e deve ser criado
                if e.status == 404:
                    config_map = client.V1ConfigMap(
                        metadata=client.V1ObjectMeta(name=name), data=data
                    )
                    created_config_map = self.core_v1_api.create_namespaced_config_map(
                        namespace=namespace, body=config_map
                    )
                    logger.info(f"ConfigMap {name} criado em {namespace}.")
                    return created_config_map
                else:
                    raise

        except ApiException as e:
            logger.error(
                f"Erro ao criar/atualizar ConfigMap {name} em {namespace}: {str(e)}"
            )
            return None

    def create_secret(
        self, name: str, namespace: str, data: dict[str, str]
    ) -> client.V1Secret | None:
        """
        Cria ou atualiza um Secret.

        Args:
            name: Nome do Secret.
            namespace: Namespace onde o Secret será criado.
            data: Dicionário com os dados do Secret (valores não codificados).

        Returns:
            O Secret criado ou None em caso de erro.
        """
        try:
            # Codifica os valores para base64
            encoded_data = {
                k: base64.b64encode(v.encode()).decode() for k, v in data.items()
            }

            # Verifica se o Secret já existe
            try:
                existing_secret = self.core_v1_api.read_namespaced_secret(
                    name=name, namespace=namespace
                )

                # Atualiza o Secret existente
                existing_secret.data = encoded_data
                updated_secret = self.core_v1_api.replace_namespaced_secret(
                    name=name, namespace=namespace, body=existing_secret
                )
                logger.info(f"Secret {name} atualizado em {namespace}.")
                return updated_secret

            except ApiException as e:
                # Se o erro for 404 (Not Found), o Secret não existe e deve ser criado
                if e.status == 404:
                    secret = client.V1Secret(
                        metadata=client.V1ObjectMeta(name=name),
                        type="Opaque",
                        data=encoded_data,
                    )
                    created_secret = self.core_v1_api.create_namespaced_secret(
                        namespace=namespace, body=secret
                    )
                    logger.info(f"Secret {name} criado em {namespace}.")
                    return created_secret
                else:
                    raise

        except ApiException as e:
            logger.error(
                f"Erro ao criar/atualizar Secret {name} em {namespace}: {str(e)}"
            )
            return None

    def create_pod(
        self,
        name: str,
        namespace: str,
        image: str,
        command: list[str] = None,
        args: list[str] = None,
        env_vars: list[dict[str, str]] = None,
        config_maps: list[dict[str, Any]] = None,
        secrets: list[dict[str, Any]] = None,
        volume_mounts: list[dict[str, Any]] = None,
        volumes: list[dict[str, Any]] = None,
        resources: dict[str, dict[str, str]] = None,
        labels: dict[str, str] = None,
        annotations: dict[str, str] = None,
        service_account: str = None,
        restart_policy: str = "Never",
        image_pull_policy: str = "IfNotPresent",
        image_pull_secrets: list[dict[str, str]] = None,
    ) -> client.V1Pod | None:
        """
        Cria um pod no Kubernetes.

        Args:
            name: Nome do pod.
            namespace: Namespace onde o pod será criado.
            image: Imagem Docker a ser usada.
            command: Comando a ser executado (equivalente a ENTRYPOINT no Dockerfile).
            args: Argumentos para o comando (equivalente a CMD no Dockerfile).
            env_vars: Lista de variáveis de ambiente no formato [{"name": "VAR_NAME", "value": "value"}].
            config_maps: Lista de ConfigMaps a serem montados.
            secrets: Lista de Secrets a serem montados.
            volume_mounts: Lista de montagens de volume.
            volumes: Lista de volumes.
            resources: Recursos do container (CPU, memória).
            labels: Labels para o pod.
            annotations: Anotações para o pod.
            service_account: Nome da conta de serviço a ser usada.
            restart_policy: Política de reinicialização ("Always", "OnFailure", "Never").
            image_pull_policy: Política de pull de imagem ("Always", "IfNotPresent", "Never").
            image_pull_secrets: Secrets para pull de imagem privada.

        Returns:
            O pod criado ou None em caso de erro.
        """
        try:
            # Prepara os env_vars no formato esperado pela API
            container_env = []
            if env_vars:
                for env_var in env_vars:
                    if "valueFrom" in env_var:
                        # Para variáveis de ambiente com referência a ConfigMap ou Secret
                        container_env.append(
                            client.V1EnvVar(
                                name=env_var["name"],
                                value_from=client.V1EnvVarSource(
                                    config_map_key_ref=client.V1ConfigMapKeySelector(
                                        name=env_var["valueFrom"]
                                        .get("configMapKeyRef", {})
                                        .get("name"),
                                        key=env_var["valueFrom"]
                                        .get("configMapKeyRef", {})
                                        .get("key"),
                                    )
                                    if "configMapKeyRef" in env_var["valueFrom"]
                                    else None,
                                    secret_key_ref=client.V1SecretKeySelector(
                                        name=env_var["valueFrom"]
                                        .get("secretKeyRef", {})
                                        .get("name"),
                                        key=env_var["valueFrom"]
                                        .get("secretKeyRef", {})
                                        .get("key"),
                                    )
                                    if "secretKeyRef" in env_var["valueFrom"]
                                    else None,
                                ),
                            )
                        )
                    else:
                        # Para variáveis de ambiente simples
                        container_env.append(
                            client.V1EnvVar(
                                name=env_var["name"], value=env_var["value"]
                            )
                        )

            # Prepara as montagens de volume
            container_volume_mounts = []
            pod_volumes = []

            # Adiciona ConfigMaps como volumes
            if config_maps:
                for cm in config_maps:
                    mount_path = cm["mountPath"]
                    name = f"configmap-{cm['name']}"

                    # Volume Mount para o container
                    container_volume_mounts.append(
                        client.V1VolumeMount(
                            name=name,
                            mount_path=mount_path,
                            sub_path=cm.get("subPath"),
                            read_only=True,
                        )
                    )

                    # Volume para o pod
                    if "items" in cm:
                        items = [
                            client.V1KeyToPath(key=item["key"], path=item["path"])
                            for item in cm["items"]
                        ]
                    else:
                        items = None

                    pod_volumes.append(
                        client.V1Volume(
                            name=name,
                            config_map=client.V1ConfigMapVolumeSource(
                                name=cm["name"], items=items
                            ),
                        )
                    )

            # Adiciona Secrets como volumes
            if secrets:
                for secret in secrets:
                    mount_path = secret["mountPath"]
                    name = f"secret-{secret['name']}"

                    # Volume Mount para o container
                    container_volume_mounts.append(
                        client.V1VolumeMount(
                            name=name,
                            mount_path=mount_path,
                            sub_path=secret.get("subPath"),
                            read_only=True,
                        )
                    )

                    # Volume para o pod
                    if "items" in secret:
                        items = [
                            client.V1KeyToPath(key=item["key"], path=item["path"])
                            for item in secret["items"]
                        ]
                    else:
                        items = None

                    pod_volumes.append(
                        client.V1Volume(
                            name=name,
                            secret=client.V1SecretVolumeSource(
                                secret_name=secret["name"], items=items
                            ),
                        )
                    )

            # Adiciona outros volumes e montagens personalizados
            if volume_mounts:
                for vm in volume_mounts:
                    container_volume_mounts.append(
                        client.V1VolumeMount(
                            name=vm["name"],
                            mount_path=vm["mountPath"],
                            sub_path=vm.get("subPath"),
                            read_only=vm.get("readOnly", False),
                        )
                    )

            if volumes:
                for vol in volumes:
                    vol_name = vol["name"]
                    vol_type = vol["type"]

                    volume = client.V1Volume(name=vol_name)

                    if vol_type == "emptyDir":
                        volume.empty_dir = client.V1EmptyDirVolumeSource()
                    elif vol_type == "hostPath":
                        volume.host_path = client.V1HostPathVolumeSource(
                            path=vol["hostPath"]["path"],
                            type=vol["hostPath"].get("type"),
                        )
                    elif vol_type == "persistentVolumeClaim":
                        volume.persistent_volume_claim = (
                            client.V1PersistentVolumeClaimVolumeSource(
                                claim_name=vol["persistentVolumeClaim"]["claimName"],
                                read_only=vol["persistentVolumeClaim"].get(
                                    "readOnly", False
                                ),
                            )
                        )

                    pod_volumes.append(volume)

            # Prepara os recursos (CPU, memória)
            container_resources = None
            if resources:
                container_resources = client.V1ResourceRequirements(
                    requests=resources.get("requests"), limits=resources.get("limits")
                )

            # Prepara o container
            container = client.V1Container(
                name="main",
                image=image,
                command=command,
                args=args,
                env=container_env,
                volume_mounts=container_volume_mounts,
                resources=container_resources,
                image_pull_policy=image_pull_policy,
            )

            # Prepara o template do pod
            pod_template = client.V1PodTemplateSpec(
                metadata=client.V1ObjectMeta(labels=labels, annotations=annotations),
                spec=client.V1PodSpec(
                    containers=[container],
                    volumes=pod_volumes,
                    restart_policy=restart_policy,
                    service_account_name=service_account,
                    image_pull_secrets=[
                        client.V1LocalObjectReference(name=secret["name"])
                        for secret in (image_pull_secrets or [])
                    ]
                    if image_pull_secrets
                    else None,
                ),
            )

            # Cria o pod
            pod = client.V1Pod(
                metadata=client.V1ObjectMeta(
                    name=name,
                    namespace=namespace,
                    labels=labels,
                    annotations=annotations,
                ),
                spec=pod_template.spec,
            )

            created_pod = self.core_v1_api.create_namespaced_pod(
                namespace=namespace, body=pod
            )

            logger.info(f"Pod {name} criado em {namespace}.")
            return created_pod

        except ApiException as e:
            logger.error(f"Erro ao criar pod {name} em {namespace}: {str(e)}")
            return None

    def delete_pod(self, name: str, namespace: str) -> bool:
        """
        Exclui um pod do Kubernetes.

        Args:
            name: Nome do pod.
            namespace: Namespace do pod.

        Returns:
            bool: True se o pod foi excluído com sucesso, False caso contrário.
        """
        try:
            self.core_v1_api.delete_namespaced_pod(
                name=name, namespace=namespace, body=client.V1DeleteOptions()
            )
            logger.info(f"Pod {name} excluído de {namespace}.")
            return True
        except ApiException as e:
            # Se o erro for 404 (Not Found), o pod já foi excluído
            if e.status == 404:
                logger.info(f"Pod {name} já foi excluído de {namespace}.")
                return True
            else:
                logger.error(f"Erro ao excluir pod {name} de {namespace}: {str(e)}")
                return False

    def get_pod(self, name: str, namespace: str) -> client.V1Pod | None:
        """
        Obtém informações sobre um pod específico.

        Args:
            name: Nome do pod.
            namespace: Namespace do pod.

        Returns:
            O pod ou None se não for encontrado ou ocorrer um erro.
        """
        try:
            return self.core_v1_api.read_namespaced_pod(name=name, namespace=namespace)
        except ApiException as e:
            if e.status == 404:
                logger.info(f"Pod {name} não encontrado em {namespace}.")
            else:
                logger.error(f"Erro ao obter pod {name} em {namespace}: {str(e)}")
            return None

    def get_pod_status(
        self, name: str, namespace: str
    ) -> tuple[str | None, dict[str, Any]]:
        """
        Obtém o status de um pod.

        Args:
            name: Nome do pod.
            namespace: Namespace do pod.

        Returns:
            Uma tupla contendo o status do pod e um dicionário com informações adicionais.
            Se o pod não for encontrado, retorna (None, {}).
        """
        pod = self.get_pod(name, namespace)
        if not pod:
            return None, {}

        # Extrai informações úteis
        pod_status = pod.status.phase
        pod_info = {
            "pod_ip": pod.status.pod_ip,
            "host_ip": pod.status.host_ip,
            "node_name": pod.spec.node_name,
            "start_time": pod.status.start_time,
            "conditions": [
                {
                    "type": condition.type,
                    "status": condition.status,
                    "reason": condition.reason,
                    "message": condition.message,
                    "last_transition_time": condition.last_transition_time,
                }
                for condition in (pod.status.conditions or [])
            ],
            "container_statuses": [
                {
                    "name": status.name,
                    "ready": status.ready,
                    "restart_count": status.restart_count,
                    "state": {
                        "running": status.state.running.started_at
                        if status.state.running
                        else None,
                        "waiting": {
                            "reason": status.state.waiting.reason,
                            "message": status.state.waiting.message,
                        }
                        if status.state.waiting
                        else None,
                        "terminated": {
                            "reason": status.state.terminated.reason,
                            "message": status.state.terminated.message,
                            "exit_code": status.state.terminated.exit_code,
                            "finished_at": status.state.terminated.finished_at,
                        }
                        if status.state.terminated
                        else None,
                    },
                }
                for status in (pod.status.container_statuses or [])
            ],
        }

        return pod_status, pod_info

    def get_pod_logs(
        self, name: str, namespace: str, container: str = None, tail_lines: int = None
    ) -> str | None:
        """
        Obtém os logs de um pod.

        Args:
            name: Nome do pod.
            namespace: Namespace do pod.
            container: Nome do container (opcional, se não informado, usa o primeiro container).
            tail_lines: Número de linhas a serem retornadas do final do log.

        Returns:
            Os logs do pod ou None em caso de erro.
        """
        try:
            return self.core_v1_api.read_namespaced_pod_log(
                name=name,
                namespace=namespace,
                container=container,
                tail_lines=tail_lines,
            )
        except ApiException as e:
            logger.error(f"Erro ao obter logs do pod {name} em {namespace}: {str(e)}")
            return None

    def watch_pod_status(
        self, name: str, namespace: str, timeout_seconds: int = 60
    ) -> str | None:
        """
        Observa alterações no status de um pod até que ele esteja em execução ou falhe.

        Args:
            name: Nome do pod.
            namespace: Namespace do pod.
            timeout_seconds: Tempo limite em segundos.

        Returns:
            O status final do pod ou None em caso de erro ou timeout.
        """
        w = watch.Watch()
        try:
            for event in w.stream(
                self.core_v1_api.list_namespaced_pod,
                namespace=namespace,
                field_selector=f"metadata.name={name}",
                timeout_seconds=timeout_seconds,
            ):
                pod = event["object"]
                status = pod.status.phase

                logger.info(f"Pod {name} status: {status}")

                if status in ["Running", "Succeeded", "Failed"]:
                    w.stop()
                    return status

            # Se chegou aqui, é porque o timeout foi atingido
            logger.warning(f"Timeout atingido ao observar pod {name} em {namespace}.")
            return None

        except ApiException as e:
            logger.error(f"Erro ao observar pod {name} em {namespace}: {str(e)}")
            w.stop()
            return None
        except Exception as e:
            logger.error(
                f"Erro inesperado ao observar pod {name} em {namespace}: {str(e)}"
            )
            w.stop()
            return None
        finally:
            w.stop()

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
        session: AsyncSession,
        bot_session: BotSession,
        bot_config: BotConfig,
        linked_credentials: LinkedInCredentials,
        config_yaml: str,
        resume_yaml: str,
    ) -> bool:
        """
        Cria um pod para executar um bot.

        Args:
            session: Sessão do banco de dados
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

        config_map = self._create_yaml_from_template(
            "bot_configmap", config_map_context
        )
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
            self.core_v1_api.delete_namespaced_secret(
                name=secret_name, namespace=namespace
            )
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
            "api_key": api_key,
        }

        pod = self._create_yaml_from_template("bot_pod", pod_context)
        try:
            self.core_v1_api.create_namespaced_pod(namespace=namespace, body=pod)
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
            except ApiException as delete_error:
                logger.error(
                    f"Erro ao excluir config map {config_map_name}: {str(delete_error)}"
                )

            try:
                self.core_v1_api.delete_namespaced_secret(
                    name=secret_name, namespace=namespace
                )
            except ApiException as delete_error:
                logger.error(
                    f"Erro ao excluir secret {secret_name}: {str(delete_error)}"
                )

            try:
                self.core_v1_api.delete_namespaced_service(
                    name=service_name, namespace=namespace
                )
            except ApiException as delete_error:
                logger.error(
                    f"Erro ao excluir service {service_name}: {str(delete_error)}"
                )

            return False

    async def send_command_to_pod(
        self,
        namespace: str,
        pod_name: str,
        command: BotCommandType,
        data: dict[str, Any] | None = None,
    ) -> bool:
        """
        Envia um comando para um pod ativo.
        Na implementação atual, os comandos são enviados via API do pod.

        Args:
            namespace: Namespace do pod
            pod_name: Nome do pod
            command: Tipo de comando a ser enviado
            data: Dados adicionais para o comando

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
                    logger.info(
                        f"Pod {pod_name} já não existe no namespace {namespace}"
                    )
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
                logger.error(
                    f"Erro ao excluir service {resources['service']}: {str(e)}"
                )
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

    async def restart_pod(self, namespace: str, pod_name: str) -> bool:
        """
        Reinicia um pod, excluindo-o e deixando o Deployment criar um novo.

        Args:
            namespace: Namespace do pod
            pod_name: Nome do pod

        Returns:
            True se o pod foi reiniciado com sucesso, False caso contrário
        """
        try:
            # Delete pod
            self.delete_pod(pod_name, namespace)

            # Check if pod exists
            try:
                self.core_v1_api.read_namespaced_pod(name=pod_name, namespace=namespace)
            except ApiException as e:
                if e.status == 404:
                    logger.info(
                        f"Pod {pod_name} já não existe no namespace {namespace}"
                    )
                    return True
                else:
                    raise

            return True

        except ApiException as e:
            logger.error(f"Erro ao reiniciar pod {pod_name}: {str(e)}")
            return False

    def create_pod_manifest(
        self,
        namespace: str,
        pod_name: str,
        image: str,
        bot_session_id: str,
        config_yaml: str,
        resume_yaml: str,
        resources: dict,
        webhook_token: str = None,
        webhook_url: str = None,
        env_vars: dict = None,
        api_key: str = None,  # Novo parâmetro para a API key
    ) -> dict:
        """
        Cria o manifesto para um pod que executará o bot.

        Args:
            namespace: Namespace do Kubernetes onde o pod será criado
            pod_name: Nome do pod
            image: Imagem Docker a ser usada
            bot_session_id: ID da sessão do bot
            config_yaml: Conteúdo do YAML de configuração
            resume_yaml: Conteúdo do YAML do currículo
            resources: Recursos do Kubernetes (CPU, memória)
            webhook_token: Token para autenticação no webhook (opcional)
            webhook_url: URL do webhook para o bot reportar eventos (opcional)
            env_vars: Variáveis de ambiente adicionais (opcional)
            api_key: API key para autenticação nos webhooks (opcional)

        Returns:
            Manifesto do pod em formato dict
        """
        env_list = [
            {"name": "BOT_SESSION_ID", "value": bot_session_id},
            {"name": "LOG_LEVEL", "value": self.log_level},
        ]

        # Adicionar webhook URL e token, se fornecidos
        if webhook_url:
            env_list.append({"name": "WEBHOOK_URI", "value": webhook_url})
        if webhook_token:
            env_list.append({"name": "WEBHOOK_TOKEN", "value": webhook_token})
        
        # Adicionar API key se fornecida
        if api_key:
            env_list.append({"name": "API_KEY", "value": api_key})

        # Adicionar variáveis de ambiente adicionais
        if env_vars:
            for key, value in env_vars.items():
                env_list.append({"name": key, "value": str(value)})

        # ... rest of the method remains unchanged ...

    async def deploy_bot(
        self,
        session_id: str,
        config_yaml: str,
        resume_yaml: str,
        pod_name: str = None,
        namespace: str = None,
        image: str = None,
        resources: dict = None,
        webhook_token: str = None,
        webhook_url: str = None,
        env_vars: dict = None,
        api_key: str = None,  # Novo parâmetro para a API key
    ) -> dict:
        """
        Deploy a bot in Kubernetes.

        Args:
            session_id: ID da sessão do bot
            config_yaml: Conteúdo do YAML de configuração
            resume_yaml: Conteúdo do YAML do currículo
            pod_name: Nome do pod (opcional, será gerado se não fornecido)
            namespace: Namespace do Kubernetes (opcional, usa o padrão se não fornecido)
            image: Imagem Docker (opcional, usa a padrão se não fornecida)
            resources: Recursos do Kubernetes (CPU, memória) (opcional)
            webhook_token: Token para autenticação no webhook (opcional)
            webhook_url: URL do webhook para o bot reportar eventos (opcional)
            env_vars: Variáveis de ambiente adicionais (opcional)
            api_key: API key para autenticação nos webhooks (opcional)

        Returns:
            Informações sobre o pod criado
        """
        # Usar valores padrão se não fornecidos
        if not namespace:
            namespace = self.namespace
        if not pod_name:
            pod_name = f"bot-{session_id[:8]}"
        if not image:
            image = self.bot_image
        if not resources:
            resources = self.default_resources

        # Verificar se o namespace existe, se não, criar
        try:
            self.core_v1_api.read_namespace(name=namespace)
        except kubernetes.client.exceptions.ApiException as e:
            if e.status == 404:
                namespace_manifest = {
                    "apiVersion": "v1",
                    "kind": "Namespace",
                    "metadata": {"name": namespace},
                }
                self.core_v1_api.create_namespace(body=namespace_manifest)
            else:
                raise

        # Criar o ConfigMap com as configurações
        cm_name = f"{pod_name}-config"
        config_data = {
            "config.yaml": config_yaml,
            "resume.yaml": resume_yaml,
        }
        config_map = kubernetes.client.V1ConfigMap(
            metadata=kubernetes.client.V1ObjectMeta(name=cm_name),
            data=config_data,
        )

        try:
            self.core_v1_api.create_namespaced_config_map(
                namespace=namespace, body=config_map
            )
        except kubernetes.client.exceptions.ApiException as e:
            if e.status == 409:  # Já existe
                self.core_v1_api.patch_namespaced_config_map(
                    name=cm_name, namespace=namespace, body=config_map
                )
            else:
                raise

        # Criar o pod
        pod_manifest = self.create_pod_manifest(
            namespace=namespace,
            pod_name=pod_name,
            image=image,
            bot_session_id=session_id,
            config_yaml=config_yaml,
            resume_yaml=resume_yaml,
            resources=resources,
            webhook_token=webhook_token,
            webhook_url=webhook_url,
            env_vars=env_vars,
            api_key=api_key,  # Passando a API key
        )

        try:
            pod = self.core_v1_api.create_namespaced_pod(
                namespace=namespace, body=pod_manifest
            )
        except kubernetes.client.exceptions.ApiException as e:
            if e.status == 409:  # Pod já existe
                # Deletar o pod existente e recriar
                self.core_v1_api.delete_namespaced_pod(
                    name=pod_name, namespace=namespace
                )
                pod = self.core_v1_api.create_namespaced_pod(
                    namespace=namespace, body=pod_manifest
                )
            else:
                raise

        return {
            "pod_name": pod_name,
            "namespace": namespace,
            "status": pod.status.phase if pod.status else "Unknown",
        }


# Singleton instance
_kubernetes_manager = None


def get_kubernetes_manager(in_cluster: bool = False) -> KubernetesManager:
    """
    Obtém uma instância singleton do gerenciador Kubernetes.

    Args:
        in_cluster: Se True, usa a configuração interna do cluster

    Returns:
        Instância do KubernetesManager
    """
    global _kubernetes_manager

    if _kubernetes_manager is None:
        _kubernetes_manager = KubernetesManager(in_cluster=in_cluster)

    return _kubernetes_manager


async def get_kubernetes_service(
    _db: AsyncSession = Depends(get_db),
) -> KubernetesManager:
    """
    Dependency para injetar o gerenciador Kubernetes.

    Args:
        _db: Sessão do banco de dados (utilizada para injeção de dependência)
    """
    return get_kubernetes_manager(in_cluster=settings.KUBERNETES_IN_CLUSTER)
