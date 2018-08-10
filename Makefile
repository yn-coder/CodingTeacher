help:
	@echo 'Makefile for Virtual Teacher project                                           '

test:
	pytest

migrate:
	flask db migrate
upgrade_db:
	flask db upgrade