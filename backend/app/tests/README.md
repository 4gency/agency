# Bot System Tests

This directory contains tests for the bot system, including:

- Service tests for the bot service
- Integration tests for the Kubernetes integration
- API tests for the bot and webhook routes
- Core tests for scheduled tasks

## Test Structure

The tests are organized as follows:

- `services/test_bot_service.py`: Tests for the bot service
- `integrations/test_kubernetes.py`: Tests for the Kubernetes integration
- `api/routes/test_bot.py`: Tests for the bot API routes
- `api/routes/test_webhooks.py`: Tests for the webhook API routes
- `core/test_scheduled_tasks.py`: Tests for the scheduled tasks

## Running the Tests

### Using Docker

The recommended way to run the tests is using Docker, which ensures all dependencies are available:

```bash
# Start the services
cd /path/to/project
docker compose up -d

# Run all tests
docker compose exec backend bash -c "cd /app && python -m pytest"

# Run specific tests with verbose output
docker compose exec backend bash -c "cd /app && python -m pytest app/tests/services/test_bot_service.py -v"

# Run tests with coverage
docker compose exec backend bash -c "cd /app && coverage run --source=app -m pytest"
docker compose exec backend bash -c "cd /app && coverage report --show-missing"
```

### Using Make

You can also use the Makefile commands:

```bash
# Run tests in development mode
make test

# Run tests with coverage
make test-prod
```

## Test Coverage

The tests aim to achieve at least 80% coverage of the bot system code. The coverage report can be generated using:

```bash
docker compose exec backend bash -c "cd /app && coverage run --source=app -m pytest"
docker compose exec backend bash -c "cd /app && coverage report --show-missing"
docker compose exec backend bash -c "cd /app && coverage html --title 'Bot System Coverage'"
```

## Mocking Strategy

The tests use mocking to isolate components:

1. **Kubernetes Integration**: The Kubernetes client is mocked to avoid actual cluster interactions.
2. **Database Sessions**: Test fixtures provide isolated database sessions.
3. **Bot Service**: Service methods are mocked in API tests to focus on route functionality.
4. **HTTP Clients**: External HTTP calls are mocked to avoid network dependencies.

## Test Fixtures

Common test fixtures include:

- `db`: Provides a database session
- `client`: Provides a FastAPI test client
- `mock_kubernetes_manager`: Mocks the Kubernetes manager
- `mock_bot_service`: Mocks the bot service
- `sample_bot_config`: Creates a sample bot configuration
- `sample_bot_session`: Creates a sample bot session
- `sample_linkedin_credentials`: Creates sample LinkedIn credentials

## Adding New Tests

When adding new tests:

1. Follow the existing pattern for test organization
2. Use appropriate mocks to isolate the component being tested
3. Ensure tests are independent and don't rely on external services
4. Add appropriate assertions to verify behavior
5. Update this README if necessary 