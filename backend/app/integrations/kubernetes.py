import json
import logging
import os
import select
import socket
from typing import Any

from kubernetes import client, config  # type: ignore
from kubernetes.client.exceptions import ApiException  # type: ignore
from kubernetes.stream import portforward  # type: ignore

from app.core.config import settings
from app.core.security import decrypt_password
from app.models.bot import BotSession, Credentials, KubernetesPodStatus

logger = logging.getLogger(__name__)


class KubernetesManager:
    """Manages communication with the Kubernetes API"""

    core_v1 = client.CoreV1Api()
    apps_v1 = client.AppsV1Api()  # API for managing Deployments

    def __init__(self) -> None:
        """Initializes the Kubernetes client"""
        try:
            if settings.KUBERNETES_IN_CLUSTER:
                config.load_incluster_config()
            else:
                # Check if kubeconfig file exists before trying to load it
                kubeconfig_path = "kubeconfig.yaml"
                if not os.path.exists(kubeconfig_path):
                    raise FileNotFoundError(
                        f"Kubeconfig file not found at {kubeconfig_path}"
                    )

                config.load_kube_config(config_file=kubeconfig_path)

                # ensure clients after connection
                self.core_v1 = client.CoreV1Api()
                self.apps_v1 = client.AppsV1Api()

            self.initialized = True

            # Verify and create namespace if necessary
            self.ensure_namespace_exists()
        except Exception as e:
            if settings.ENVIRONMENT == "production":
                # Only raise an exception in production environment
                raise Exception(
                    f"Failed to initialize Kubernetes client: {str(e)}"
                ) from e
            else:
                # For staging and local environments, log the error but don't stop the application
                logger.warning(f"Kubernetes client initialization failed: {str(e)}")
                self.initialized = False

    def ensure_namespace_exists(self) -> None:
        """Checks if the namespace exists and creates it if necessary"""
        if not self.initialized:
            logger.warning(
                "Cannot ensure namespace exists: Kubernetes client not initialized"
            )
            return

        try:
            self.core_v1.read_namespace(name=settings.KUBERNETES_NAMESPACE)
            logger.info(f"Namespace {settings.KUBERNETES_NAMESPACE} already exists")
        except ApiException as e:
            if e.status == 404:
                namespace = client.V1Namespace(
                    metadata=client.V1ObjectMeta(name=settings.KUBERNETES_NAMESPACE)
                )
                self.core_v1.create_namespace(body=namespace)
                logger.info(f"Namespace {settings.KUBERNETES_NAMESPACE} created")
            else:
                logger.error(f"Error checking namespace: {str(e)}")
                raise

    def create_bot_deployment(self, session: BotSession) -> tuple[bool, str]:
        """Creates a deployment for a bot session"""
        if not self.initialized:
            return False, "Kubernetes client not initialized"

        deployment_name = session.kubernetes_pod_name
        user_id = session.user_id
        credentials = session.credentials
        style = session.style.value
        applies_limit = session.applies_limit

        try:
            # Create deployment definition
            deployment = client.V1Deployment(
                metadata=client.V1ObjectMeta(
                    name=deployment_name,
                    namespace=settings.KUBERNETES_NAMESPACE,
                    labels={
                        "app": "bot-applier",
                        "session-id": str(session.id),
                        "user-id": str(user_id),
                    },
                ),
                spec=client.V1DeploymentSpec(
                    replicas=1,  # Starts with 1 replica (active)
                    selector=client.V1LabelSelector(
                        match_labels={"bot-deployment": deployment_name}
                    ),
                    template=client.V1PodTemplateSpec(
                        metadata=client.V1ObjectMeta(
                            labels={
                                "app": "bot-applier",
                                "bot-deployment": deployment_name,
                                "session-id": str(session.id),
                                "user-id": str(user_id),
                            }
                        ),
                        spec=client.V1PodSpec(
                            restart_policy="Always",
                            containers=[
                                client.V1Container(
                                    name="bot",
                                    image=settings.BOT_IMAGE,
                                    ports=[client.V1ContainerPort(container_port=5000)],
                                    resources=client.V1ResourceRequirements(
                                        requests={
                                            "cpu": settings.BOT_DEFAULT_CPU_REQUEST,
                                            "memory": settings.BOT_DEFAULT_MEMORY_REQUEST,
                                        },
                                        limits={
                                            "cpu": settings.BOT_DEFAULT_CPU_LIMIT,
                                            "memory": settings.BOT_DEFAULT_MEMORY_LIMIT,
                                        },
                                    ),
                                    env=[
                                        client.V1EnvVar(name="API_PORT", value="5000"),
                                        client.V1EnvVar(
                                            name="LINKEDIN_EMAIL",
                                            value=credentials.email,
                                        ),
                                        client.V1EnvVar(
                                            name="LINKEDIN_PASSWORD",
                                            value=decrypt_password(
                                                credentials.password
                                            ),
                                        ),
                                        client.V1EnvVar(
                                            name="APPLY_LIMIT", value=str(applies_limit)
                                        ),
                                        client.V1EnvVar(
                                            name="STYLE_CHOICE", value=style
                                        ),
                                        client.V1EnvVar(
                                            name="SEC_CH_UA",
                                            value='""Google Chrome";v="111", "Not(A:Brand";v="8", "Chromium";v="111""',
                                        ),
                                        client.V1EnvVar(
                                            name="SEC_CH_UA_PLATFORM", value="Windows"
                                        ),
                                        client.V1EnvVar(
                                            name="USER_AGENT",
                                            value="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/111.0.0.0 Safari/537.36",
                                        ),
                                        client.V1EnvVar(
                                            name="BACKEND_TOKEN",
                                            value=session.api_key,
                                        ),
                                        client.V1EnvVar(
                                            name="BACKEND_URL",
                                            value=settings.BACKEND_HOST,
                                        ),
                                        client.V1EnvVar(
                                            name="BOT_ID", value=str(session.id)
                                        ),
                                        client.V1EnvVar(
                                            name="GOTENBERG_URL",
                                            value="http://gotenberg:3000",
                                        ),
                                    ],
                                )
                            ],
                        ),
                    ),
                ),
            )

            # Create the deployment in Kubernetes
            response = self.apps_v1.create_namespaced_deployment(
                namespace=settings.KUBERNETES_NAMESPACE, body=deployment
            )

            if not response:
                logger.error(f"Error creating deployment: {response.__dict__}")
                return False, str(response)

            # Create a service to access the bot
            service = client.V1Service(
                metadata=client.V1ObjectMeta(
                    name=deployment_name, namespace=settings.KUBERNETES_NAMESPACE
                ),
                spec=client.V1ServiceSpec(
                    selector={"bot-deployment": deployment_name},
                    ports=[client.V1ServicePort(port=5000, target_port=5000)],
                ),
            )

            self.core_v1.create_namespaced_service(
                namespace=settings.KUBERNETES_NAMESPACE, body=service
            )

            logger.info(
                f"Deployment {deployment_name} created in namespace {settings.KUBERNETES_NAMESPACE}"
            )
            return True, deployment_name

        except Exception as e:
            logger.error(f"Error creating deployment: {str(e)}")
            return False, str(e)

    def pause_bot(self, deployment_name: str) -> tuple[bool, str | None]:
        """Pauses a bot by scaling the deployment to 0 replicas"""
        if not self.initialized:
            return False, "Kubernetes client not initialized"

        try:
            # Get current deployment
            deployment = self.apps_v1.read_namespaced_deployment(
                name=deployment_name, namespace=settings.KUBERNETES_NAMESPACE
            )

            # Scale to 0 replicas
            deployment.spec.replicas = 0

            # Update the deployment
            self.apps_v1.patch_namespaced_deployment(
                name=deployment_name,
                namespace=settings.KUBERNETES_NAMESPACE,
                body=deployment,
            )

            logger.info(f"Bot {deployment_name} paused (scaled to 0 replicas)")
            return True, None
        except ApiException as e:
            if e.status == 404:
                logger.warning(f"Deployment {deployment_name} not found for pausing")
                return False, "Deployment not found"
            logger.error(f"Error pausing bot: {str(e)}")
            return False, str(e)

    def resume_bot(self, deployment_name: str) -> tuple[bool, str | None]:
        """Resumes a bot by scaling the deployment to 1 replica"""
        if not self.initialized:
            return False, "Kubernetes client not initialized"

        try:
            # Get current deployment
            deployment = self.apps_v1.read_namespaced_deployment(
                name=deployment_name, namespace=settings.KUBERNETES_NAMESPACE
            )

            # Scale to 1 replica
            deployment.spec.replicas = 1

            # Update the deployment
            self.apps_v1.patch_namespaced_deployment(
                name=deployment_name,
                namespace=settings.KUBERNETES_NAMESPACE,
                body=deployment,
            )

            logger.info(f"Bot {deployment_name} resumed (scaled to 1 replica)")
            return True, None
        except ApiException as e:
            if e.status == 404:
                logger.warning(f"Deployment {deployment_name} not found for resuming")
                return False, "Deployment not found"
            logger.error(f"Error resuming bot: {str(e)}")
            return False, str(e)

    def delete_bot(self, deployment_name: str) -> tuple[bool, str | None]:
        """Removes a bot (deployment and service)"""
        if not self.initialized:
            return False, "Kubernetes client not initialized"

        try:
            # Delete the deployment
            self.apps_v1.delete_namespaced_deployment(
                name=deployment_name, namespace=settings.KUBERNETES_NAMESPACE
            )

            # Delete the associated service
            try:
                self.core_v1.delete_namespaced_service(
                    name=deployment_name, namespace=settings.KUBERNETES_NAMESPACE
                )
            except ApiException as e:
                if e.status != 404:  # Ignore if service doesn't exist
                    logger.warning(
                        f"Error deleting service {deployment_name}: {str(e)}"
                    )

            logger.info(
                f"Bot {deployment_name} deleted from namespace {settings.KUBERNETES_NAMESPACE}"
            )
            return True, "Bot deleted successfully"
        except ApiException as e:
            if e.status == 404:
                logger.warning(f"Deployment {deployment_name} not found for deletion")
                return True, "Deployment not found"
            logger.error(f"Error deleting bot: {str(e)}")
            return False, str(e)

    def get_bot_status(
        self, deployment_name: str
    ) -> tuple[KubernetesPodStatus | None, str | None]:
        """Gets the current status of a bot"""
        if not self.initialized:
            return None, "Kubernetes client not initialized"

        try:
            # Check deployment
            deployment = self.apps_v1.read_namespaced_deployment(
                name=deployment_name, namespace=settings.KUBERNETES_NAMESPACE
            )

            # Check if active or paused
            replicas = deployment.spec.replicas
            available_replicas = deployment.status.available_replicas

            if replicas == 0:
                status = KubernetesPodStatus.PAUSED
            elif available_replicas is not None and available_replicas > 0:
                status = KubernetesPodStatus.RUNNING
            else:
                status = KubernetesPodStatus.STARTING

            # Get pod IP if active
            pod_ip = None
            if status == KubernetesPodStatus.RUNNING:
                pods = self.core_v1.list_namespaced_pod(
                    namespace=settings.KUBERNETES_NAMESPACE,
                    label_selector=f"bot-deployment={deployment_name}",
                )
                if pods.items and len(pods.items) > 0:
                    pod_ip = pods.items[0].status.pod_ip

            return status, pod_ip

        except ApiException as e:
            if e.status == 404:
                return None, "Bot not found"
            logger.error(f"Error getting bot status: {str(e)}")
            return None, str(e)

    def update_bot_config(
        self,
        deployment_name: str,
        credentials: Credentials | None = None,
        style: str | None = None,
        applies_limit: int | None = None,
    ) -> tuple[bool, str | None]:
        """Updates the configuration of an existing bot"""
        if not self.initialized:
            return False, "Kubernetes client not initialized"

        try:
            # Get current deployment
            deployment = self.apps_v1.read_namespaced_deployment(
                name=deployment_name, namespace=settings.KUBERNETES_NAMESPACE
            )

            # Update environment variables as needed
            container = deployment.spec.template.spec.containers[0]

            # Helper function to update env vars
            def update_env_var(name: str, value: Any) -> None:
                if value is None:
                    return

                for i, env_var in enumerate(container.env):
                    if env_var.name == name:
                        container.env[i].value = str(value)
                        return

                # If not found, add the variable
                container.env.append(client.V1EnvVar(name=name, value=str(value)))

            # Update environment variables
            if credentials:
                update_env_var("LINKEDIN_EMAIL", credentials.email)
                update_env_var("LINKEDIN_PASSWORD", credentials.password)

            if style is not None:
                update_env_var("STYLE_CHOICE", style)

            if applies_limit is not None:
                update_env_var("APPLY_LIMIT", applies_limit)

            # Apply changes
            self.apps_v1.patch_namespaced_deployment(
                name=deployment_name,
                namespace=settings.KUBERNETES_NAMESPACE,
                body=deployment,
            )

            logger.info(f"Bot configuration {deployment_name} updated")
            return True, "Configuration updated successfully"
        except ApiException as e:
            if e.status == 404:
                logger.warning(f"Deployment {deployment_name} not found for update")
                return False, "Deployment not found"
            logger.error(f"Error updating bot: {str(e)}")
            return False, str(e)

    def get_all_bots(self) -> list[dict[str, Any]]:
        """Lists all bots (deployments) in the namespace"""
        if not self.initialized:
            return []

        try:
            deployments = self.apps_v1.list_namespaced_deployment(
                namespace=settings.KUBERNETES_NAMESPACE,
                label_selector="app=bot-applier",
            )

            bots = []
            for deployment in deployments.items:
                name = deployment.metadata.name
                status, pod_ip = self.get_bot_status(name)
                session_id = deployment.metadata.labels.get("session-id", "Unknown")
                user_id = deployment.metadata.labels.get("user-id", "Unknown")

                bots.append(
                    {
                        "name": name,
                        "status": status,
                        "pod_ip": pod_ip,
                        "session_id": session_id,
                        "user_id": user_id,
                        "replicas": deployment.spec.replicas,
                    }
                )

            return bots
        except Exception as e:
            logger.error(f"Error listing bots: {str(e)}")
            return []

    def send_request_to_bot(
        self,
        deployment_name: str,
        method: str,
        endpoint: str,
        target_port: int = 5000,
        data: dict[str, Any] | None = None,
        headers: dict[str, str] | None = None,
        timeout: int = 10,
    ) -> tuple[bool, str, int | None]:
        """
        Sends an HTTP request to a bot pod using port forwarding

        Args:
            deployment_name: Name of the bot deployment
            method: HTTP method (GET, POST, PUT, DELETE, etc.)
            endpoint: Path to API endpoint (e.g., "/api/status")
            target_port: Target port on the pod
            data: Optional request data (dict or string)
            headers: Optional dictionary of HTTP headers
            timeout: Request timeout in seconds

        Returns:
            tuple: (success, response_data, status_code)
                - success: Boolean indicating if the request was successful
                - response_data: Response content if successful, error message if not
                - status_code: HTTP status code or None if request failed
        """
        if not self.initialized:
            return False, "Kubernetes client not initialized", None

        try:
            # Get pod information from the deployment
            pods = self.core_v1.list_namespaced_pod(
                namespace=settings.KUBERNETES_NAMESPACE,
                label_selector=f"bot-deployment={deployment_name}",
            )

            if not pods.items or len(pods.items) == 0:
                return (
                    False,
                    f"No active pods found for deployment {deployment_name}",
                    None,
                )

            pod_name = pods.items[0].metadata.name

            # Set up port forwarding directly with the socket approach
            pf = portforward(
                self.core_v1.connect_get_namespaced_pod_portforward,
                name=pod_name,
                namespace=settings.KUBERNETES_NAMESPACE,
                ports=str(target_port),
            )

            try:
                # Get socket for the target port
                sock = pf.socket(target_port)
                sock.setblocking(True)

                # Prepare headers
                if headers is None:
                    headers = {}

                # Convert dict data to JSON if needed
                request_body = ""
                if isinstance(data, dict):
                    if "Content-Type" not in headers:
                        headers["Content-Type"] = "application/json"
                    if headers.get("Content-Type") == "application/json":
                        request_body = json.dumps(data)
                elif data is not None:
                    request_body = data

                # Build HTTP request
                request_lines = [f"{method.upper()} {endpoint} HTTP/1.1"]
                request_lines.append("Host: localhost")
                for header_name, header_value in headers.items():
                    request_lines.append(f"{header_name}: {header_value}")

                if request_body:
                    request_lines.append(f"Content-Length: {len(request_body)}")

                request_lines.append("Connection: close")
                request_lines.append("")
                request_lines.append(request_body if request_body else "")

                # Send the request
                http_request = "\r\n".join(request_lines).encode("utf-8")
                sock.sendall(http_request)

                # Receive the response
                response_data = b""
                while True:
                    ready_to_read, _, _ = select.select([sock], [], [], timeout)
                    if not ready_to_read:
                        raise TimeoutError(f"Request timed out after {timeout} seconds")

                    chunk = sock.recv(4096)
                    if not chunk:
                        break
                    response_data += chunk

                # Parse the response
                raw_response = response_data.decode("utf-8")

                # Split headers and body
                header_end = raw_response.find("\r\n\r\n")
                if header_end == -1:
                    return False, "Invalid HTTP response", None

                headers_text = raw_response[:header_end]
                body_text = raw_response[header_end + 4 :]

                # Extract status code
                status_line = headers_text.split("\r\n")[0]
                status_parts = status_line.split(" ", 2)
                if len(status_parts) < 3:
                    return False, f"Invalid HTTP status line: {status_line}", None

                status_code = int(status_parts[1])

                # Try to parse JSON response
                try:
                    parsed_response = json.loads(body_text)
                except (ValueError, TypeError):
                    parsed_response = body_text

                success = 200 <= status_code < 300
                return success, parsed_response, status_code

            finally:
                # Always close the socket and stop port forwarding
                sock.close()
                pf.close()

        except TimeoutError as e:
            logger.error(f"Request timeout: {str(e)}")
            return False, f"Request timeout: {str(e)}", None
        except json.JSONDecodeError as e:
            logger.error(f"JSON parse error: {str(e)}")
            return (
                False,
                f"Response parse error: {str(e)}",
                status_code if "status_code" in locals() else None,
            )
        except Exception as e:
            logger.error(f"Error sending request to bot: {str(e)}")
            return False, f"Error: {str(e)}", None

    def _find_available_port(
        self, start_port: int = 49152, end_port: int = 65535
    ) -> int:
        """Find an available local port for port forwarding"""
        for port in range(start_port, end_port):
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                if s.connect_ex(("localhost", port)) != 0:
                    return port

        # If no ports are available, use a default port and hope for the best
        return 49152


kubernetes_manager = KubernetesManager()
