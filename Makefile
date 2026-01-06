.PHONY: up down logs restart chaos verify

up:
	docker-compose -f deploy/docker-compose.yml up -d

down:
	docker-compose -f deploy/docker-compose.yml down

logs:
	docker-compose -f deploy/docker-compose.yml logs -f freqtrade

restart: down up

chaos:
	python scripts/risk/chaos_test.py

verify:
	python scripts/verify_deployment.py
