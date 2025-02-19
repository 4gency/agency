.PHONY: help run stop lint test format

# Variables for common commands and paths
DOCKER_COMPOSE := docker compose
BACKEND        := backend
SCRIPTS_DIR    := /app/scripts

# The macro takes two parameters:
#   $(1): The script name (without extension)
#   $(2): Optional extra arguments
define run_script
	@echo "Running $(1) code $(if $(2),with args: $(2))"
	$(DOCKER_COMPOSE) exec -T $(BACKEND) bash $(SCRIPTS_DIR)/$(1).sh $(2)
endef

help:
	@echo "Available commands:"
	@echo "  make help             - Show this help message"
	@echo "  make run              - Start the services"
	@echo "  make stop             - Stop and remove the services"
	@echo "  make lint             - Run linting"
	@echo "  make test [ARGS=...]   - Run tests, optionally pass extra args (e.g. ARGS='-s -v')"
	@echo "  make format           - Format code"

run:
	$(DOCKER_COMPOSE) up -d

stop:
	$(DOCKER_COMPOSE) down -v --remove-orphans

lint:
	$(call run_script,lint)

test:
	$(call run_script,test-dev,$(ARGS))

format:
	$(call run_script,format)

console:
	$(DOCKER_COMPOSE) exec $(BACKEND) bash
