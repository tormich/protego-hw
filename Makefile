# Makefile for Alembic database migrations

# Variables
ALEMBIC := uv run alembic

# Default target
.PHONY: help
help:
	@echo "Available commands:"
	@echo "  make migrate-create name='migration name'  - Create a new migration"
	@echo "  make migrate-auto name='migration name'    - Create a new migration with auto-detected changes"
	@echo "  make migrate-up                           - Run all pending migrations"
	@echo "  make migrate-up-one                       - Run only the next pending migration"
	@echo "  make migrate-down                         - Rollback the most recent migration"
	@echo "  make migrate-history                      - Show migration history"
	@echo "  make migrate-current                      - Show current migration version"
	@echo "  make migrate-stamp rev='revision'         - Stamp the database with the given revision"

# Create a new empty migration
.PHONY: migrate-create
migrate-create:
	@if [ -z "$(name)" ]; then \
		echo "Error: Migration name is required. Use make migrate-create name='migration name'"; \
		exit 1; \
	fi
	$(ALEMBIC) revision -m "$(name)"

# Create a new migration with auto-detected changes
.PHONY: migrate-auto
migrate-auto:
	@if [ -z "$(name)" ]; then \
		echo "Error: Migration name is required. Use make migrate-auto name='migration name'"; \
		exit 1; \
	fi
	$(ALEMBIC) revision --autogenerate -m "$(name)"

# Run all pending migrations
.PHONY: migrate-up
migrate-up:
	$(ALEMBIC) upgrade head

# Run only the next pending migration
.PHONY: migrate-up-one
migrate-up-one:
	$(ALEMBIC) upgrade +1

# Rollback the most recent migration
.PHONY: migrate-down
migrate-down:
	$(ALEMBIC) downgrade -1

# Show migration history
.PHONY: migrate-history
migrate-history:
	$(ALEMBIC) history

# Show current migration version
.PHONY: migrate-current
migrate-current:
	$(ALEMBIC) current

# Stamp the database with the given revision without running migrations
.PHONY: migrate-stamp
migrate-stamp:
	@if [ -z "$(rev)" ]; then \
		echo "Error: Revision is required. Use make migrate-stamp rev='revision'"; \
		exit 1; \
	fi
	$(ALEMBIC) stamp $(rev)