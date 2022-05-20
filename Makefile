default: test

test-all:
	docker-compose -f smsAutomation/docker-compose.test.yaml up -V --abort-on-container-exit --build tests-py38 && \
	docker-compose -f smsAutomation/docker-compose.test.yaml up -V --abort-on-container-exit --build tests-py39  && \
	docker-compose -f smsAutomation/docker-compose.test.yaml up -V --abort-on-container-exit --build tests-py310

test:
	poetry run pytest .

lint:
	poetry run flake8 fastapi_metadata && \
	poetry run pylint fastapi_metadata

install:
	poetry install

coverage:
	poetry run pytest . --cov-report term --cov-report html:build/cov_html --cov=fastapi_metadata

format:
	poetry run black . && \
	poetry run isort --profile black .