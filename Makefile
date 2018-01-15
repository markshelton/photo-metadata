#######################################################################
# PREAMBLE
#######################################################################

MAKEFLAGS += --warn-undefined-variables
SHELL := bash
.SHELLFLAGS := -eu -o pipefail -c
.DEFAULT_GOAL := start
.DELETE_ON_ERROR:
.SUFFIXES:
CURRENT_DIR = $(shell echo $(CURDIR) | sed 's|^/[^/]*||')

#######################################################################
# APP CONFIGURATION
#######################################################################

APP_CONFIG_PATH = ./.env
include $(APP_CONFIG_PATH)
export $(shell sed 's/=.*//' $(APP_CONFIG_PATH))

#######################################################################
# IMAGE CONFIGURATION
#######################################################################

IMAGE_CONFIG_PATH = ./src/config/image.env
include $(IMAGE_CONFIG_PATH)
export $(shell sed 's/=.*//' $(IMAGE_CONFIG_PATH))

#######################################################################
# APP COMMANDS
#######################################################################

.PHONY: start
start: up shell

.PHONY: stop
stop:
	-docker exec -it \
		$(CONTAINER_APP_NAME) \
		bash -c "pip3 freeze > $(REQUIREMENTS_PATH)"
	-docker-compose \
		--file docker-compose.$(ENV).yml down

.PHONY: restart
restart: stop start

.PHONY: up
up: volume _up

.PHONY: _up
_up: 
	PROJECT_DIR=$(CURRENT_DIR) \
	CONTAINER_APP_NAME=$(CONTAINER_APP_NAME) \
	CONTAINER_DB_NAME=$(CONTAINER_DB_NAME) \
	VOLUME_DB_NAME=$(VOLUME_DB_NAME) \
	DB_IMAGE=$(DB_IMAGE) \
	DB_VERSION=$(DB_VERSION) \
	docker-compose \
		--file docker-compose.$(ENV).yml \
		up --build -d
	

#######################################################################

.PHONY: jupyter
jupyter:
	explorer.exe "http://localhost:8888/tree"

.PHONY: shell
shell:
	docker exec -it $(CONTAINER_APP_NAME) $(SHELL)

.PHONY: volume
volume:
	-docker volume create --name=$(VOLUME_DB_NAME)

#######################################################################
# IMAGE COMMANDS
#######################################################################

.PHONY: prebuild
prebuild:
	npm list -g dockerignore --depth=0 || npm install -g dockerignore
	dockerignore -g="$(GIT_IGNORE_PATH)" -D="$(DOCKER_IGNORE_PATH)"

.PHONY: build
build: prebuild _build

.PHONY: _build
_build:
	TENSORFLOW_VERSION=$(TENSORFLOW_VERSION) \
	OPENCV_VERSION=$(OPENCV_VERSION) \
	DLIB_VERSION=$(DLIB_VERSION) \
	docker build \
		-t $(IMAGE_NAME) \
		-f $(DOCKER_FILE_PATH) \
		$(BUILD_CONTEXT)

#######################################################################

.PHONY: push
push: version tag publish

.PHONY: publish
publish: repo-login publish-latest publish-version

.PHONY: publish-latest
publish-latest: 
	docker push $(IMAGE_NAME)\:latest

.PHONY: publish-version
publish-version: 
	docker push $(IMAGE_NAME)\:$(VERSION)

.PHONY: repo-login
repo-login: 
	docker login -u $(REPO_NAME)

.PHONY: tag
tag: tag-latest tag-version

.PHONY: tag-latest
tag-latest: 
	docker tag $(IMAGE_NAME) $(IMAGE_NAME)\:latest

.PHONY: tag-version
tag-version: 
	docker tag $(IMAGE_NAME) $(IMAGE_NAME)\:$(VERSION)

.PHONY: version
version:
	@echo $(VERSION)

#######################################################################