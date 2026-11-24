.PHONY: up down backend-test

up:
	docker compose up --build -d
	docker compose ps

down:
	docker compose down

backend-test:
	cd backend && pytest
