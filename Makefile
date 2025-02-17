.PHONY: help lint test format

define run_script
	@echo "$(1) code"
	docker compose exec -T backend bash /app/scripts/$(1).sh
endef

help:
	@echo "make help"

run:
	docker compose up -d

stop:
	docker compose down -v --remove-orphans

lint:
	$(call run_script,lint)

test:
	$(call run_script,test)

format:
	$(call run_script,format)
