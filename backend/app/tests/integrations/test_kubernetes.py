from collections.abc import Generator, MutableMapping
from unittest.mock import MagicMock, patch

import pytest
from kubernetes.client.exceptions import ApiException  # type: ignore

from app.core.config import settings
from app.integrations.kubernetes import KubernetesManager
from app.models.bot import BotSession, Credentials, KubernetesPodStatus

# Type for the mock_kubernetes fixture return
KubernetesMocks = MutableMapping[str, MagicMock]


@pytest.fixture
def mock_kubernetes() -> Generator[KubernetesMocks, None, None]:
    """Fixture to mock Kubernetes client components"""
    with patch("app.integrations.kubernetes.client") as mock_client, patch(
        "app.integrations.kubernetes.config"
    ) as mock_config:
        mock_core_v1 = MagicMock()
        mock_apps_v1 = MagicMock()
        mock_client.CoreV1Api.return_value = mock_core_v1
        mock_client.AppsV1Api.return_value = mock_apps_v1

        # Setup mock namespace
        mock_namespace = MagicMock()
        mock_metadata = MagicMock()
        mock_metadata.name = settings.KUBERNETES_NAMESPACE
        mock_namespace.metadata = mock_metadata
        mock_client.V1Namespace.return_value = mock_namespace
        mock_client.V1ObjectMeta.return_value = mock_metadata

        yield {
            "client": mock_client,
            "config": mock_config,
            "core_v1": mock_core_v1,
            "apps_v1": mock_apps_v1,
        }


@pytest.fixture
def kubernetes_manager_patched(mock_kubernetes: KubernetesMocks) -> KubernetesManager:
    """
    Create a KubernetesManager with mocked components and patch initialized status
    """
    # Patch os.path.exists to return True for kubeconfig
    with patch("os.path.exists", return_value=True):
        manager = KubernetesManager()
        # Force initialized to True
        manager.initialized = True
        # Set the mocked API instances
        manager.core_v1 = mock_kubernetes["core_v1"]
        manager.apps_v1 = mock_kubernetes["apps_v1"]
        return manager


def test_ensure_namespace_exists_existing(
    kubernetes_manager_patched: KubernetesManager, mock_kubernetes: KubernetesMocks
) -> None:
    """Test ensure_namespace_exists when namespace already exists"""
    # Set up the mock to return success
    mock_kubernetes["core_v1"].read_namespace.return_value = MagicMock()

    # Call the method
    kubernetes_manager_patched.ensure_namespace_exists()

    # Verify expected calls
    mock_kubernetes["core_v1"].read_namespace.assert_called_once_with(
        name=settings.KUBERNETES_NAMESPACE
    )
    mock_kubernetes["core_v1"].create_namespace.assert_not_called()


def test_ensure_namespace_exists_create(
    kubernetes_manager_patched: KubernetesManager, mock_kubernetes: KubernetesMocks
) -> None:
    """Test ensure_namespace_exists when namespace needs to be created"""
    # Set up mock to raise 404
    api_exception = ApiException(status=404)
    mock_kubernetes["core_v1"].read_namespace.side_effect = api_exception

    # Call the method
    kubernetes_manager_patched.ensure_namespace_exists()

    # Verify expected calls
    mock_kubernetes["core_v1"].read_namespace.assert_called_once_with(
        name=settings.KUBERNETES_NAMESPACE
    )
    mock_kubernetes["core_v1"].create_namespace.assert_called_once()


def test_ensure_namespace_other_api_exception(
    kubernetes_manager_patched: KubernetesManager, mock_kubernetes: KubernetesMocks
) -> None:
    """Test ensure_namespace_exists when there's a non-404 API exception"""
    # Set up mock to raise 500
    api_exception = ApiException(status=500)
    mock_kubernetes["core_v1"].read_namespace.side_effect = api_exception

    # Verify exception is raised
    with pytest.raises(ApiException):
        kubernetes_manager_patched.ensure_namespace_exists()


def test_create_bot_deployment_success(
    kubernetes_manager_patched: KubernetesManager, mock_kubernetes: KubernetesMocks
) -> None:
    """Test creating a bot deployment successfully"""
    # Mock session
    session = MagicMock(spec=BotSession)
    session.kubernetes_pod_name = "test-deployment"
    session.user_id = "user-123"
    session.credentials = MagicMock(spec=Credentials)
    session.credentials.email = "test@example.com"
    session.credentials.password = "encrypted-password"
    session.style.value = "professional"
    session.applies_limit = 10
    session.id = "session-123"
    session.api_key = "api-key-123"

    # Mock API responses
    mock_kubernetes["apps_v1"].create_namespaced_deployment.return_value = MagicMock(
        status=200
    )

    # Mock decrypt_password
    with patch(
        "app.integrations.kubernetes.decrypt_password",
        return_value="decrypted-password",
    ):
        success, name = kubernetes_manager_patched.create_bot_deployment(session)

    # Verify results
    assert success
    assert name == "test-deployment"

    # Verify API calls
    mock_kubernetes["apps_v1"].create_namespaced_deployment.assert_called_once()
    mock_kubernetes["core_v1"].create_namespaced_service.assert_called_once()


def test_create_bot_deployment_exception(
    kubernetes_manager_patched: KubernetesManager, mock_kubernetes: KubernetesMocks
) -> None:
    """Test creating a bot deployment with exception"""
    # Mock session
    session = MagicMock(spec=BotSession)
    session.kubernetes_pod_name = "test-deployment"

    # Mock exception
    mock_kubernetes["apps_v1"].create_namespaced_deployment.side_effect = Exception(
        "API error"
    )

    # Mock decrypt_password
    with patch(
        "app.integrations.kubernetes.decrypt_password",
        return_value="decrypted-password",
    ):
        success, error = kubernetes_manager_patched.create_bot_deployment(session)

    # Verify results
    assert not success
    assert error == "API error"


def test_pause_bot_success(
    kubernetes_manager_patched: KubernetesManager, mock_kubernetes: KubernetesMocks
) -> None:
    """Test pausing a bot successfully"""
    # Mock deployment
    deployment = MagicMock()
    mock_kubernetes["apps_v1"].read_namespaced_deployment.return_value = deployment

    # Call method
    success, error = kubernetes_manager_patched.pause_bot("test-deployment")

    # Verify results
    assert success
    assert error is None

    # Verify deployment modifications
    assert deployment.spec.replicas == 0
    mock_kubernetes["apps_v1"].patch_namespaced_deployment.assert_called_once()


def test_pause_bot_not_found(
    kubernetes_manager_patched: KubernetesManager, mock_kubernetes: KubernetesMocks
) -> None:
    """Test pausing a bot that doesn't exist"""
    # Mock 404 error
    mock_kubernetes["apps_v1"].read_namespaced_deployment.side_effect = ApiException(
        status=404
    )

    # Call method
    success, error = kubernetes_manager_patched.pause_bot("test-deployment")

    # Verify results
    assert not success
    assert error == "Deployment not found"


def test_resume_bot_success(
    kubernetes_manager_patched: KubernetesManager, mock_kubernetes: KubernetesMocks
) -> None:
    """Test resuming a bot successfully"""
    # Mock deployment
    deployment = MagicMock()
    mock_kubernetes["apps_v1"].read_namespaced_deployment.return_value = deployment

    # Call method
    success, error = kubernetes_manager_patched.resume_bot("test-deployment")

    # Verify results
    assert success
    assert error is None

    # Verify deployment modifications
    assert deployment.spec.replicas == 1
    mock_kubernetes["apps_v1"].patch_namespaced_deployment.assert_called_once()


def test_resume_bot_not_found(
    kubernetes_manager_patched: KubernetesManager, mock_kubernetes: KubernetesMocks
) -> None:
    """Test resuming a bot that doesn't exist"""
    # Mock 404 error
    mock_kubernetes["apps_v1"].read_namespaced_deployment.side_effect = ApiException(
        status=404
    )

    # Call method
    success, error = kubernetes_manager_patched.resume_bot("test-deployment")

    # Verify results
    assert not success
    assert error == "Deployment not found"


def test_delete_bot_success(
    kubernetes_manager_patched: KubernetesManager, mock_kubernetes: KubernetesMocks
) -> None:
    """Test deleting a bot successfully"""
    # Call method
    success, message = kubernetes_manager_patched.delete_bot("test-deployment")

    # Verify results
    assert success
    assert message == "Bot deleted successfully"

    # Verify API calls
    mock_kubernetes["apps_v1"].delete_namespaced_deployment.assert_called_once_with(
        name="test-deployment", namespace=settings.KUBERNETES_NAMESPACE
    )
    mock_kubernetes["core_v1"].delete_namespaced_service.assert_called_once_with(
        name="test-deployment", namespace=settings.KUBERNETES_NAMESPACE
    )


def test_delete_bot_not_found(
    kubernetes_manager_patched: KubernetesManager, mock_kubernetes: KubernetesMocks
) -> None:
    """Test deleting a bot that doesn't exist"""
    # Mock 404 error for deployment
    mock_kubernetes["apps_v1"].delete_namespaced_deployment.side_effect = ApiException(
        status=404
    )

    # Call method
    success, message = kubernetes_manager_patched.delete_bot("test-deployment")

    # Verify results (should still be success for this edge case)
    assert success
    assert message == "Deployment not found"


def test_get_bot_status_running(
    kubernetes_manager_patched: KubernetesManager, mock_kubernetes: KubernetesMocks
) -> None:
    """Test getting status of a running bot"""
    # Mock deployment with running status
    deployment = MagicMock()
    deployment.spec.replicas = 1
    deployment.status.available_replicas = 1
    mock_kubernetes["apps_v1"].read_namespaced_deployment.return_value = deployment

    # Mock pod info
    pod = MagicMock()
    pod.status.pod_ip = "10.0.0.1"
    pod_list = MagicMock()
    pod_list.items = [pod]
    mock_kubernetes["core_v1"].list_namespaced_pod.return_value = pod_list

    # Call method
    status, pod_ip = kubernetes_manager_patched.get_bot_status("test-deployment")

    # Verify results
    assert status == KubernetesPodStatus.RUNNING
    assert pod_ip == "10.0.0.1"


def test_get_bot_status_paused(
    kubernetes_manager_patched: KubernetesManager, mock_kubernetes: KubernetesMocks
) -> None:
    """Test getting status of a paused bot"""
    # Mock deployment with paused status
    deployment = MagicMock()
    deployment.spec.replicas = 0
    deployment.status.available_replicas = None
    mock_kubernetes["apps_v1"].read_namespaced_deployment.return_value = deployment

    # Call method
    status, pod_ip = kubernetes_manager_patched.get_bot_status("test-deployment")

    # Verify results
    assert status == KubernetesPodStatus.PAUSED
    assert pod_ip is None


def test_get_bot_status_starting(
    kubernetes_manager_patched: KubernetesManager, mock_kubernetes: KubernetesMocks
) -> None:
    """Test getting status of a starting bot"""
    # Mock deployment with starting status
    deployment = MagicMock()
    deployment.spec.replicas = 1
    deployment.status.available_replicas = None
    mock_kubernetes["apps_v1"].read_namespaced_deployment.return_value = deployment

    # Call method
    status, pod_ip = kubernetes_manager_patched.get_bot_status("test-deployment")

    # Verify results
    assert status == KubernetesPodStatus.STARTING
    assert pod_ip is None


def test_get_bot_status_not_found(
    kubernetes_manager_patched: KubernetesManager, mock_kubernetes: KubernetesMocks
) -> None:
    """Test getting status of a non-existent bot"""
    # Mock 404 error
    mock_kubernetes["apps_v1"].read_namespaced_deployment.side_effect = ApiException(
        status=404
    )

    # Call method
    status, error = kubernetes_manager_patched.get_bot_status("test-deployment")

    # Verify results
    assert status is None
    assert error == "Bot not found"


def test_update_bot_config_success(
    kubernetes_manager_patched: KubernetesManager, mock_kubernetes: KubernetesMocks
) -> None:
    """Test updating bot configuration successfully"""
    # Mock deployment
    deployment = MagicMock()
    container = MagicMock()

    # Create MagicMock objects for environment variables
    linkedin_email = MagicMock()
    linkedin_email.name = "LINKEDIN_EMAIL"
    linkedin_email.value = "old@example.com"

    linkedin_password = MagicMock()
    linkedin_password.name = "LINKEDIN_PASSWORD"
    linkedin_password.value = "old-password"

    style_choice = MagicMock()
    style_choice.name = "STYLE_CHOICE"
    style_choice.value = "old-style"

    apply_limit = MagicMock()
    apply_limit.name = "APPLY_LIMIT"
    apply_limit.value = "5"

    container.env = [
        linkedin_email,
        linkedin_password,
        style_choice,
        apply_limit,
    ]
    deployment.spec.template.spec.containers = [container]
    mock_kubernetes["apps_v1"].read_namespaced_deployment.return_value = deployment

    # Mock credentials
    credentials = MagicMock(spec=Credentials)
    credentials.email = "new@example.com"
    credentials.password = "new-password"

    # Call method
    success, message = kubernetes_manager_patched.update_bot_config(
        "test-deployment", credentials=credentials, style="new-style", applies_limit=10
    )

    # Verify results
    assert success
    assert message == "Configuration updated successfully"

    # Verify environment variables were updated
    assert linkedin_email.value == "new@example.com"
    assert linkedin_password.value == "new-password"
    assert style_choice.value == "new-style"
    assert apply_limit.value == "10"

    # Verify deployment was patched
    mock_kubernetes["apps_v1"].patch_namespaced_deployment.assert_called_once()


def test_update_bot_config_not_found(
    kubernetes_manager_patched: KubernetesManager, mock_kubernetes: KubernetesMocks
) -> None:
    """Test updating config of a non-existent bot"""
    # Mock 404 error
    mock_kubernetes["apps_v1"].read_namespaced_deployment.side_effect = ApiException(
        status=404
    )

    # Call method
    success, error = kubernetes_manager_patched.update_bot_config("test-deployment")

    # Verify results
    assert not success
    assert error == "Deployment not found"


def test_get_all_bots(
    kubernetes_manager_patched: KubernetesManager, mock_kubernetes: KubernetesMocks
) -> None:
    """Test getting all bots"""
    # Mock deployments
    deployment1 = MagicMock()
    deployment1.metadata.name = "deployment-1"
    deployment1.metadata.labels = {"session-id": "session-1", "user-id": "user-1"}
    deployment1.spec.replicas = 1

    deployment2 = MagicMock()
    deployment2.metadata.name = "deployment-2"
    deployment2.metadata.labels = {"session-id": "session-2", "user-id": "user-2"}
    deployment2.spec.replicas = 0

    deployment_list = MagicMock()
    deployment_list.items = [deployment1, deployment2]
    mock_kubernetes["apps_v1"].list_namespaced_deployment.return_value = deployment_list

    # Mock get_bot_status for each deployment
    with patch.object(
        kubernetes_manager_patched,
        "get_bot_status",
        side_effect=[
            (KubernetesPodStatus.RUNNING, "10.0.0.1"),
            (KubernetesPodStatus.PAUSED, None),
        ],
    ):
        bots = kubernetes_manager_patched.get_all_bots()

    # Verify results
    assert len(bots) == 2
    assert bots[0]["name"] == "deployment-1"
    assert bots[0]["status"] == KubernetesPodStatus.RUNNING
    assert bots[0]["pod_ip"] == "10.0.0.1"
    assert bots[0]["session_id"] == "session-1"
    assert bots[0]["user_id"] == "user-1"
    assert bots[0]["replicas"] == 1

    assert bots[1]["name"] == "deployment-2"
    assert bots[1]["status"] == KubernetesPodStatus.PAUSED
    assert bots[1]["pod_ip"] is None
    assert bots[1]["session_id"] == "session-2"
    assert bots[1]["user_id"] == "user-2"
    assert bots[1]["replicas"] == 0


def test_send_request_to_bot_no_pods(
    kubernetes_manager_patched: KubernetesManager, mock_kubernetes: KubernetesMocks
) -> None:
    """Test sending a request when no pods are found"""
    # Mock empty pod list
    pod_list = MagicMock()
    pod_list.items = []
    mock_kubernetes["core_v1"].list_namespaced_pod.return_value = pod_list

    # Call method
    success, error, status_code = kubernetes_manager_patched.send_request_to_bot(
        "test-deployment", "GET", "/status"
    )

    # Verify results
    assert not success
    assert "No active pods found" in error
    assert status_code is None


@patch("socket.socket")
def test_find_available_port(
    mock_socket: MagicMock, kubernetes_manager_patched: KubernetesManager
) -> None:
    """Test finding an available port"""
    # Mock socket connection to fail (port available)
    mock_socket_instance = MagicMock()
    mock_socket_instance.connect_ex.return_value = 1
    mock_socket.return_value.__enter__.return_value = mock_socket_instance

    # Call method
    port = kubernetes_manager_patched._find_available_port(
        start_port=12345, end_port=12350
    )

    # Verify results
    assert port == 12345
    mock_socket_instance.connect_ex.assert_called_once_with(("localhost", 12345))
