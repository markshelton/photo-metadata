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
.PHONY:
	start stop restart up _up \
	jupyter shell volume \
	prebuild build _build \
	push repo-login version \
	publish publish-latest publish-version \
	tag tag-latest tag-version 

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

start: up shell

stop:
	-docker exec -it $(CONTAINER_APP_NAME) bash -c "pip3 freeze > $(REQUIREMENTS_PATH)"
	-docker-compose --file docker-compose.$(ENV).yml down

restart: stop start

up: volume _up

_up: 
	PROJECT_DIR=$(CURRENT_DIR) \
	CONTAINER_APP_NAME=$(CONTAINER_APP_NAME) \
	CONTAINER_DB_NAME=$(CONTAINER_DB_NAME) \
	VOLUME_DB_NAME=$(VOLUME_DB_NAME) \
	APP_IMAGE=$(APP_IMAGE) \
	APP_VERSION=$(APP_VERSION) \
	DB_IMAGE=$(DB_IMAGE) \
	DB_VERSION=$(DB_VERSION) \
	docker-compose --file docker-compose.$(ENV).yml up --build -d

#######################################################################

jupyter:
	explorer.exe "http://localhost:8888/tree"

shell:
	docker exec -it $(CONTAINER_APP_NAME) $(SHELL)

volume:
	-docker volume create --name=$(VOLUME_DB_NAME)

#######################################################################
# IMAGE COMMANDS
#######################################################################

prebuild:
	npm list -g dockerignore --depth=0 || npm install -g dockerignore
	dockerignore -g="$(GIT_IGNORE_PATH)" -D="$(DOCKER_IGNORE_PATH)"

build: prebuild _build

_build:
	TENSORFLOW_VERSION=$(TENSORFLOW_VERSION) \
	OPENCV_VERSION=$(OPENCV_VERSION) \
	DLIB_VERSION=$(DLIB_VERSION) \
	docker build -t $(IMAGE_NAME) -f $(DOCKER_FILE_PATH) $(BUILD_CONTEXT)

#######################################################################

push: version tag publish

repo-login: 
	docker login -u $(REPO_NAME)

version:
	@echo $(VERSION)

#######################################################################

publish: repo-login publish-latest publish-version

publish-latest: 
	docker push $(IMAGE_NAME)\:latest

publish-version: 
	docker push $(IMAGE_NAME)\:$(VERSION)

#######################################################################

tag: tag-latest tag-version

tag-latest: 
	docker tag $(IMAGE_NAME) $(IMAGE_NAME)\:latest

tag-version: 
	docker tag $(IMAGE_NAME) $(IMAGE_NAME)\:$(VERSION)

#######################################################################