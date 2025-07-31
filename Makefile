SHELL := /bin/bash
# Makefile for Docker project
.PHONY: all default up down build build_up start stop restart logs clean dev devb help

# Configuration
DOCKER_COMPOSE := docker compose
DEV_COMPOSE_FILE := docker-compose.yml
PROD_COMPOSE_FILE := docker-compose-prod.yml

# Default to development environment
env ?= dev

# Determine the compose file based on the environment
COMPOSE_FILE := $(if $(filter prod,$(env)),$(PROD_COMPOSE_FILE),$(DEV_COMPOSE_FILE))

# Default target
all: help

help:
	@echo "Usage:"
	@echo "  make up [env=dev|prod]       - Start and restart services (default: dev)"
	@echo "  make down [env=dev|prod]     - Stop and remove services (default: dev)"
	@echo "  make build [env=dev|prod]    - Build or rebuild services (default: dev)"
	@echo "  make build_up [env=dev|prod] - Build or rebuild services and start services (default: dev)"
	@echo "  make start [env=dev|prod]    - Start previously stopped services (default: dev)"
	@echo "  make stop [env=dev|prod]     - Stop services (default: dev)"
	@echo "  make restart [env=dev|prod]  - Restart services (default: dev)"
	@echo "  make logs [env=dev|prod]     - View logs from services (default: dev)"
	@echo "  make init                    - Pulls models inside the Ollama container"
	@echo "  make dev                     - Run development environment with logs"
	@echo "  make test                    - Test API endpoints using NewMan"
	@echo ""
	@echo "Examples:"
	@echo "  make up env=dev     - Use development compose file"
	@echo "  make up env=prod    - Use production compose file"
	@echo "  make dev            - Quick development setup"


dev:
	$(DOCKER_COMPOSE) -f $(DEV_COMPOSE_FILE) build --parallel && \
	$(DOCKER_COMPOSE) -f $(DEV_COMPOSE_FILE) up --remove-orphans

init:
	$(DOCKER_COMPOSE) -f $(DEV_COMPOSE_FILE) up -d ollama
	docker exec -it ollama /bin/bash ./entrypoint.sh
	$(DOCKER_COMPOSE) -f $(COMPOSE_FILE) down ollama

test:
	docker run --rm -v ./static/tests:/etc/newman --network aatmun -t postman/newman run aatmunn_api_collection

# Standard Docker Compose commands
up:
	$(DOCKER_COMPOSE) -f $(COMPOSE_FILE) up -d

down:
	$(DOCKER_COMPOSE) -f $(COMPOSE_FILE) down

build:
	$(DOCKER_COMPOSE) -f $(COMPOSE_FILE) build --parallel

build_up:
	$(DOCKER_COMPOSE) -f $(COMPOSE_FILE) up --build -d

start:
	$(DOCKER_COMPOSE) -f $(COMPOSE_FILE) start

stop:
	$(DOCKER_COMPOSE) -f $(COMPOSE_FILE) stop

restart:
	$(DOCKER_COMPOSE) -f $(COMPOSE_FILE) restart

logs:
	$(DOCKER_COMPOSE) -f $(COMPOSE_FILE) logs -f