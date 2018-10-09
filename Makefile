help:
	@echo 'Makefile for Virtual Teacher project                                           '

test:
	pytest
cov:
	py.test --cov=app
migrate:
	flask db migrate
upgrade_db:
	flask db upgrade