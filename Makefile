.PHONY: dev test test-docker demo

dev:
	docker compose up --build

test:
	cd backend && uv sync --extra dev && uv run pytest -v

test-docker:
	docker compose run --rm backend uv run --extra dev pytest -v

demo:
	docker compose up --build -d
	@echo ""
	@echo "  Frontend : http://localhost:5173"
	@echo "  Backend  : http://localhost:8000"
	@echo "  API docs : http://localhost:8000/docs"
	@echo ""
