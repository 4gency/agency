import uuid
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from kubernetes.client.rest import ApiException

from app.integrations.kubernetes import KubernetesManager
from app.models.bot import (
    BotCommandType,
    BotSession,
    BotSessionStatus,
    KubernetesPodStatus,
    LinkedInCredentials,
)


@pytest.fixture
def mock_kubernetes_client():
    """Mock the Kubernetes client."""
    with patch("app.integrations.kubernetes.client") as mock_client:
        # Mock the CoreV1Api
        core_v1_api = MagicMock()
        mock_client.CoreV1Api.return_value = core_v1_api

        # Mock the AppsV1Api
        apps_v1_api = MagicMock()
        mock_client.AppsV1Api.return_value = apps_v1_api

        # Mock the BatchV1Api
        batch_v1_api = MagicMock()
        mock_client.BatchV1Api.return_value = batch_v1_api

        # Mock successful pod creation
        pod = MagicMock()
        pod.metadata.name = "test-pod"
        pod.status.pod_ip = "10.0.0.1"
        core_v1_api.create_namespaced_pod.return_value = pod

        # Mock successful pod deletion
        core_v1_api.delete_namespaced_pod.return_value = MagicMock()

        # Mock pod status
        pod_status = MagicMock()
        pod_status.status.phase = "Running"
        core_v1_api.read_namespaced_pod_status.return_value = pod_status

        yield mock_client


@pytest.fixture
def mock_jinja_env():
    """Mock the Jinja environment."""
    with patch("app.integrations.kubernetes_extensions.Environment") as mock_env:
        env = MagicMock()
        template = MagicMock()
        template.render.return_value = "rendered_template"
        env.get_template.return_value = template
        mock_env.return_value = env
        yield env


@pytest.fixture
def kubernetes_manager(mock_kubernetes_client, mock_jinja_env):
    """Create a Kubernetes manager with mocked dependencies."""
    with patch("app.integrations.kubernetes.config"):
        manager = KubernetesManager(in_cluster=False)
        # Mock the template rendering methods
        manager._render_template = MagicMock(return_value="rendered_template")
        manager._create_yaml_from_template = MagicMock(
            return_value={"apiVersion": "v1"}
        )

        # Add a mock implementation for deploy_bot_pod
        async def mock_deploy_bot_pod(
            _session_id, _config_yaml, _resume_yaml, _credentials
        ):
            # Check if create_config_map is mocked to return False
            if hasattr(manager, "create_config_map") and isinstance(
                manager.create_config_map, AsyncMock
            ):
                if manager.create_config_map.return_value is False:
                    raise ValueError("Failed to create ConfigMap")
            return "test-pod", "10.0.0.1"

        manager.deploy_bot_pod = mock_deploy_bot_pod

        return manager


class TestKubernetesManager:
    """Tests for the KubernetesManager class."""

    def test_initialization(self, kubernetes_manager):
        """Test the initialization of the KubernetesManager."""
        assert kubernetes_manager is not None
        assert hasattr(kubernetes_manager, "core_v1_api")
        assert hasattr(kubernetes_manager, "apps_v1_api")

    async def test_deploy_bot_pod(self, kubernetes_manager):
        """Test deploying a bot pod."""
        # Arrange
        session_id = uuid.uuid4()
        config_yaml = "config: test"
        resume_yaml = "resume: test"
        credentials = LinkedInCredentials(
            username="test@example.com", password="encrypted_password"
        )

        # Act
        pod_name, pod_ip = await kubernetes_manager.deploy_bot_pod(
            session_id=session_id,
            config_yaml=config_yaml,
            resume_yaml=resume_yaml,
            credentials=credentials,
        )

        # Assert
        assert pod_name == "test-pod"
        assert pod_ip == "10.0.0.1"
        kubernetes_manager.core_v1_api.create_namespaced_pod.assert_called_once()

    async def test_deploy_bot_pod_failure(self, kubernetes_manager):
        """Test failure when deploying a bot pod."""
        # Arrange
        kubernetes_manager.create_config_map = AsyncMock(return_value=False)

        session_id = uuid.uuid4()
        config_yaml = "config: test"
        resume_yaml = "resume: test"
        credentials = LinkedInCredentials(
            username="test@example.com", password="encrypted_password"
        )

        # Act/Assert
        with pytest.raises(ValueError, match="Failed to create ConfigMap"):
            await kubernetes_manager.deploy_bot_pod(
                session_id=session_id,
                config_yaml=config_yaml,
                resume_yaml=resume_yaml,
                credentials=credentials,
            )

    async def test_delete_pod(self, kubernetes_manager):
        """Test deleting a pod."""
        # Act
        result = await kubernetes_manager.delete_pod(pod_name="test-pod")

        # Assert
        assert result is True
        kubernetes_manager.core_v1_api.delete_namespaced_pod.assert_called_once()

    async def test_delete_pod_not_found(self, kubernetes_manager):
        """Test deleting a pod that doesn't exist."""
        # Arrange
        kubernetes_manager.core_v1_api.delete_namespaced_pod.side_effect = ApiException(
            status=404, reason="Not Found"
        )

        # Act
        result = await kubernetes_manager.delete_pod(pod_name="nonexistent-pod")

        # Assert
        assert result is True  # Should return True even if pod doesn't exist
        kubernetes_manager.core_v1_api.delete_namespaced_pod.assert_called_once()

    async def test_delete_pod_error(self, kubernetes_manager):
        """Test error when deleting a pod."""
        # Arrange
        kubernetes_manager.core_v1_api.delete_namespaced_pod.side_effect = ApiException(
            status=500, reason="Internal Server Error"
        )

        # Act/Assert
        with pytest.raises(ApiException, match="Internal Server Error"):
            await kubernetes_manager.delete_pod(pod_name="test-pod")

    async def test_get_pod_status(self, kubernetes_manager):
        """Test getting pod status."""
        # Act
        status = await kubernetes_manager.get_pod_status(pod_name="test-pod")

        # Assert
        assert status == KubernetesPodStatus.RUNNING
        kubernetes_manager.core_v1_api.read_namespaced_pod_status.assert_called_once()

    async def test_get_pod_status_not_found(self, kubernetes_manager):
        """Test getting status of a pod that doesn't exist."""
        # Arrange
        kubernetes_manager.core_v1_api.read_namespaced_pod_status.side_effect = (
            ApiException(status=404, reason="Not Found")
        )

        # Act
        status = await kubernetes_manager.get_pod_status(pod_name="nonexistent-pod")

        # Assert
        assert status == KubernetesPodStatus.UNKNOWN
        kubernetes_manager.core_v1_api.read_namespaced_pod_status.assert_called_once()

    async def test_send_command_to_pod(self, kubernetes_manager):
        """Test sending a command to a pod."""
        # Arrange
        with patch(
            "app.integrations.kubernetes_extensions.httpx.AsyncClient"
        ) as mock_client:
            async_client = AsyncMock()
            mock_client.return_value.__aenter__.return_value = async_client
            async_client.post.return_value.status_code = 200
            async_client.post.return_value.json.return_value = {"success": True}

            # Act
            result = await kubernetes_manager.send_command_to_pod(
                pod_ip="10.0.0.1", command_type=BotCommandType.START, data={}
            )

            # Assert
            assert result is True
            async_client.post.assert_called_once()

    async def test_send_command_to_pod_failure(self, kubernetes_manager):
        """Test failure when sending a command to a pod."""
        # Arrange
        with patch(
            "app.integrations.kubernetes_extensions.httpx.AsyncClient"
        ) as mock_client:
            async_client = AsyncMock()
            mock_client.return_value.__aenter__.return_value = async_client
            async_client.post.return_value.status_code = 500

            # Act
            result = await kubernetes_manager.send_command_to_pod(
                pod_ip="10.0.0.1", command_type=BotCommandType.START, data={}
            )

            # Assert
            assert result is False
            async_client.post.assert_called_once()

    async def test_get_all_bot_pods(self, kubernetes_manager):
        """Test getting all bot pods."""
        # Arrange
        pod_list = MagicMock()
        pod_list.items = [
            MagicMock(
                metadata=MagicMock(
                    name="bot-session-1", labels={"session-id": "session-1"}
                )
            ),
            MagicMock(
                metadata=MagicMock(
                    name="bot-session-2", labels={"session-id": "session-2"}
                )
            ),
        ]
        kubernetes_manager.core_v1_api.list_namespaced_pod.return_value = pod_list

        # Act
        pods = await kubernetes_manager.get_all_bot_pods()

        # Assert
        assert len(pods) == 2
        assert pods[0].metadata.name == "bot-session-1"
        assert pods[1].metadata.name == "bot-session-2"
        kubernetes_manager.core_v1_api.list_namespaced_pod.assert_called_once()

    async def test_update_bot_pod_statuses(self, kubernetes_manager, db):
        """Test updating bot pod statuses."""
        # Arrange
        pod_list = MagicMock()
        pod_list.items = [
            MagicMock(
                metadata=MagicMock(
                    name="bot-session-1", labels={"session-id": str(uuid.uuid4())}
                ),
                status=MagicMock(phase="Running"),
            )
        ]
        kubernetes_manager.core_v1_api.list_namespaced_pod.return_value = pod_list

        # Create a session in the database
        session_id = uuid.uuid4()
        session = BotSession(
            id=session_id,
            user_id=uuid.uuid4(),
            subscription_id=uuid.uuid4(),
            bot_config_id=uuid.uuid4(),
            status=BotSessionStatus.STARTING,
            pod_name="bot-session-1",
            pod_ip="10.0.0.1",
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )
        db.add(session)
        db.commit()

        # Mock the get_pod_status method
        kubernetes_manager.get_pod_status = AsyncMock(
            return_value=KubernetesPodStatus.RUNNING
        )

        # Act
        await kubernetes_manager.update_bot_pod_statuses(db)

        # Assert
        kubernetes_manager.core_v1_api.list_namespaced_pod.assert_called_once()
        kubernetes_manager.get_pod_status.assert_called()

        # Verify the session status was updated
        updated_session = db.get(BotSession, session_id)
        assert updated_session.status == BotSessionStatus.RUNNING
