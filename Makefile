help:
	@echo 'Makefile for Virtual Teacher project                                           '

test:
	pytest

migrate:
	flask db migrate