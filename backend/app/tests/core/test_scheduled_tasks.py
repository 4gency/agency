from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest

from app.core.scheduled_tasks import (
    ScheduledTaskManager,
    _task_manager,
    start_scheduled_tasks,
    stop_scheduled_tasks,
)


@pytest.fixture
def mock_httpx_client():
    """Mock the httpx client."""
    with patch("app.core.scheduled_tasks.httpx.AsyncClient") as mock_client:
        async_client = AsyncMock()
        mock_client.return_value.__aenter__.return_value = async_client
        async_client.post.return_value.status_code = 200
        async_client.post.return_value.json.return_value = {"success": True}
        yield async_client


@pytest.fixture
def task_manager(mock_httpx_client):
    """Create a task manager with mocked dependencies."""
    manager = ScheduledTaskManager()
    # Set a short update interval for testing
    manager.update_interval = 1  # Use an integer value for the interval
    return manager


class TestScheduledTasks:
    """Tests for the scheduled tasks."""

    def test_start_stop_task_manager(self, task_manager):
        """Test starting and stopping the task manager."""
        # Test starting
        assert not task_manager.running
        task_manager.start()
        assert task_manager.running
        assert task_manager._thread is not None

        # Test stopping
        task_manager.stop()
        assert not task_manager.running
        assert task_manager._thread is not None  # Thread is still there but not running

    def test_start_when_already_running(self, task_manager):
        """Test starting the task manager when it's already running."""
        # Start the task manager
        task_manager.start()
        assert task_manager.running

        # Try to start it again
        task_manager.start()
        # Should still be running
        assert task_manager.running

        # Clean up
        task_manager.stop()

    def test_stop_when_not_running(self, task_manager):
        """Test stopping the task manager when it's not running."""
        # Task manager should not be running initially
        assert not task_manager.running

        # Try to stop it
        task_manager.stop()
        # Should still not be running
        assert not task_manager.running

    def test_update_bot_statuses(self, task_manager, mock_httpx_client):
        """Test the _update_bot_statuses method."""
        # Call the method
        task_manager._update_bot_statuses()

        # Verify the API call was made
        mock_httpx_client.post.assert_called_once()

        # Check the URL and headers
        call_args = mock_httpx_client.post.call_args
        assert "/api/v1/webhooks/status-update" in call_args[0][0]
        assert "X-API-Key" in call_args[1]["headers"]

    def test_update_bot_statuses_error(self, task_manager, mock_httpx_client):
        """Test error handling in _update_bot_statuses method."""
        # Arrange
        mock_httpx_client.post.side_effect = httpx.RequestError("Connection error")

        # Act - should not raise an exception
        task_manager._update_bot_statuses()

        # Assert
        mock_httpx_client.post.assert_called_once()

    def test_run_tasks(self, task_manager):
        """Test the _run_tasks method."""
        # Mock the _update_bot_statuses method
        task_manager._update_bot_statuses = MagicMock()

        # Create a flag to stop the task after a few iterations
        def stop_after_calls(*_args, **_kwargs):
            task_manager.running = False
            return None

        # Make update_bot_statuses stop the loop after being called
        task_manager._update_bot_statuses.side_effect = stop_after_calls

        # Run the tasks - this will exit after one iteration due to our mock
        task_manager._run_tasks()

        # Verify _update_bot_statuses was called
        task_manager._update_bot_statuses.assert_called_once()

    def test_start_scheduled_tasks(self):
        """Test the start_scheduled_tasks function."""
        # Mock the task manager
        with patch("app.core.scheduled_tasks._task_manager") as mock_manager:
            # Call the function
            start_scheduled_tasks()

            # Verify the task manager was started
            mock_manager.start.assert_called_once()

    def test_stop_scheduled_tasks(self):
        """Test the stop_scheduled_tasks function."""
        # Mock the task manager
        with patch("app.core.scheduled_tasks._task_manager") as mock_manager:
            # Call the function
            stop_scheduled_tasks()

            # Verify the task manager was stopped
            mock_manager.stop.assert_called_once()

    def test_task_manager_singleton(self):
        """Test that _task_manager is a singleton."""
        # Get the global task manager
        manager1 = _task_manager

        # Import it again
        from app.core.scheduled_tasks import _task_manager as manager2

        # They should be the same object
        assert manager1 is manager2
