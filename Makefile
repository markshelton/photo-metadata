#######################################################################
# LIBRARY COMMANDS
#######################################################################

.PHONY: init test

init:
	pip3 install -r requirements.txt

test:
	py.test tests

#######################################################################
# DOCUMENTATION COMMANDS
#######################################################################

DOCUMENTATION_MAKE_DIR = docs/
DOCUMENTATION_MAKE = $(MAKE) -C $(DOCUMENTATION_MAKE_DIR) 

.PHONY: docs-html docs-help

docs-html:
	$(DOCUMENTATION_MAKE) html

docs-help:
	$(DOCUMENTATION_MAKE) help

#######################################################################
# DOCKER COMPOSE COMMANDS
#######################################################################

DOCKER_COMPOSE_MAKE_DIR = docker/compose/
DOCKER_COMPOSE_MAKE = $(MAKE) -C $(DOCKER_COMPOSE_MAKE_DIR) 

.PHONY: start stop restart up freeze notebook dashboard shell

start:
	$(DOCKER_COMPOSE_MAKE) start

stop:
	$(DOCKER_COMPOSE_MAKE) stop

restart:
	$(DOCKER_COMPOSE_MAKE) restart

up:
	$(DOCKER_COMPOSE_MAKE) up

freeze:
	$(DOCKER_COMPOSE_MAKE) freeze

notebook:
	$(DOCKER_COMPOSE_MAKE) notebook

dashboard:
	$(DOCKER_COMPOSE_MAKE) dashboard

shell:
	$(DOCKER_COMPOSE_MAKE) shell

#######################################################################
# DOCKER BUILD COMMANDS
#######################################################################

DOCKER_BUILD_MAKE_DIR = docker/build/
DOCKER_BUILD_MAKE = $(MAKE) -C $(DOCKER_BUILD_MAKE_DIR) 

.PHONY: build push tag

build:
	$(DOCKER_BUILD_MAKE) build

push:
	$(DOCKER_BUILD_MAKE) push

tag:
	$(DOCKER_BUILD_MAKE) tag

#######################################################################