PYTHON = poetry run python
MANAGE = $(PYTHON) manage.py

runserver:
	$(MANAGE) runserver

migrations:
	$(MANAGE) makemigrations

migrate:
	$(MANAGE) migrate

createsuperuser:
	$(MANAGE) createsuperuser

test:
	poetry run pytest

# Usage: make createapp name=myapp
ifeq ($(OS),Windows_NT)
createapp:
	@if "$(name)"=="" (echo Usage: make createapp name=myapp & exit /b 1)
	@if not exist apps mkdir apps
	$(MANAGE) startapp $(name)
	move /Y "$(name)" "apps\$(name)" >nul
	@echo Created app apps\$(name)
else
createapp:
	@if [ -z "$(name)" ]; then echo "Usage: make createapp name=myapp"; exit 1; fi
	mkdir -p apps
	$(MANAGE) startapp $(name)
	mv "$(name)" "apps/$(name)"
	@echo "Created app apps/$(name)"
endif