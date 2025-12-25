.PHONY: help install dev test lint format clean docker-up docker-down docker-logs

help:
	@echo "Comandos disponíveis:"
	@echo "  make install      - Instalar dependências"
	@echo "  make dev          - Executar aplicação em modo desenvolvimento"
	@echo "  make test         - Executar testes"
	@echo "  make lint         - Verificar código com ruff"
	@echo "  make format       - Formatar código com black e ruff"
	@echo "  make clean        - Limpar arquivos temporários"
	@echo "  make docker-up    - Iniciar containers Docker"
	@echo "  make docker-down  - Parar containers Docker"
	@echo "  make docker-logs  - Ver logs dos containers"

install:
	pip install -r requirements.txt

dev:
	uvicorn src.main:app --reload --host 0.0.0.0 --port 8000

test:
	pytest -v --cov=src --cov-report=term-missing

lint:
	ruff check src/ tests/
	mypy src/

format:
	black src/ tests/
	ruff check --fix src/ tests/

clean:
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} +
	find . -type d -name ".pytest_cache" -exec rm -rf {} +
	find . -type d -name ".mypy_cache" -exec rm -rf {} +
	find . -type d -name ".ruff_cache" -exec rm -rf {} +
	rm -rf htmlcov/
	rm -rf .coverage

docker-up:
	docker-compose up --build -d

docker-down:
	docker-compose down

docker-logs:
	docker-compose logs -f app
