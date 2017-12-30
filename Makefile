MAKEFLAGS += --warn-undefined-variables
SHELL := bash
.SHELLFLAGS := -eu -o pipefail -c
.DEFAULT_GOAL := all
.DELETE_ON_ERROR:
.SUFFIXES:

BUILD_CONTEXT = ./src/
DOCKERIGNORE_PATH = ./src/config/.dockerignore
DOCKERFILE_PATH = ./src/config/Dockerfile
REQUIREMENTS_PATH = ./src/config/requirements.txt
PROJECT_DIR = $(shell echo $(CURDIR) | sed 's|^/[^/]*||')

CONFIG ?= ./src/config/config.env
include $(CONFIG)
export $(shell sed 's/=.*//' $(CONFIG))

APP_NAME = "$(REPO_NAME)/$(PROJECT_NAME)"

.DEFAULT_GOAL := up

.PHONY: build
build: prebuild; docker build -t $(PROJECT_NAME) -f $(DOCKERFILE_PATH) $(BUILD_CONTEXT)

.PHONY: build-nc
build-nc: prebuild; docker build --no-cache -t $(PROJECT_NAME) -f $(DOCKERFILE_PATH) $(BUILD_CONTEXT)

.PHONY: jupyter
jupyter:
	sleep 3
	-explorer.exe "http://localhost:8888/tree"

.PHONY: prebuild
prebuild:
	npm list -g dockerignore --depth=0 || npm install -g dockerignore
	dockerignore -g=".gitignore" -D="$(DOCKERIGNORE_PATH)"

.PHONY: publish
publish: repo-login publish-latest publish-version

.PHONY: publish-latest
publish-latest: 
	docker push $(APP_NAME)\:latest

.PHONY: publish-version
publish-version: 
	docker push $(APP_NAME)\:$(VERSION)

.PHONY: repo-login
repo-login: 
	docker login -u $(REPO_NAME)

.PHONY: restart
restart: stop up

.PHONY: run
run: 
	docker run -td --rm --name="$(PROJECT_NAME)" \
		-p 8888:8888 -p 6006:6006 \
		-v $(PROJECT_DIR):/home/app/ \
		$(PROJECT_NAME)

.PHONY: shell
shell:
	docker exec -it $(PROJECT_NAME) /bin/bash

.PHONY: stop
stop:
	docker exec -it $(PROJECT_NAME) /bin/bash -c "pip3 freeze > $(REQUIREMENTS_PATH)"
	-docker stop $(PROJECT_NAME)

.PHONY: tag
tag: tag-latest tag-version

.PHONY: tag-latest
tag-latest: 
	docker tag $(PROJECT_NAME) $(APP_NAME)\:latest

.PHONY: tag-version
tag-version: 
	docker tag $(PROJECT_NAME) $(APP_NAME)\:$(VERSION)

.PHONY: up
up: build run jupyter shell

.PHONY: version
version:
	@echo $(VERSION)