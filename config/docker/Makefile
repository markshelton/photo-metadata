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
	prebuild build _build \
	push repo-login version \
	publish publish-latest publish-version \
	tag tag-latest tag-version 

#######################################################################
# LIBRARY CONFIGURATION
#######################################################################

LIBRARY_CONFIG_PATH = ../CONFIG.env
include $(LIBRARY_CONFIG_PATH)
export $(shell sed 's/=.*//' $(LIBRARY_CONFIG_PATH))

#######################################################################
# IMAGE CONFIGURATION
#######################################################################

IMAGE_CONFIG_PATH = ./image.env
include $(IMAGE_CONFIG_PATH)
export $(shell sed 's/=.*//' $(IMAGE_CONFIG_PATH))

#######################################################################
# IMAGE COMMANDS
#######################################################################

prebuild:
	npm list -g dockerignore --depth=0 || npm install -g dockerignore
	dockerignore -g="$(GIT_IGNORE_PATH)" -D="$(DOCKER_IGNORE_PATH)"

build: _build

_build:
	TENSORFLOW_VERSION=$(TENSORFLOW_VERSION) \
	OPENCV_VERSION=$(OPENCV_VERSION) \
	DLIB_VERSION=$(DLIB_VERSION) \
	docker build -t $(APP_IMAGE) -f $(DOCKER_FILE_PATH) $(BUILD_CONTEXT)

#######################################################################

push: version tag publish

repo-login: 
	docker login -u $(REPO_NAME)

version:
	@echo $(APP_VERSION)

#######################################################################

publish: repo-login publish-latest publish-version

publish-latest: 
	docker push $(APP_IMAGE)\:latest

publish-version: 
	docker push $(APP_IMAGE)\:$(APP_VERSION)

#######################################################################

tag: tag-latest tag-version

tag-latest: 
	docker tag $(APP_IMAGE) $(APP_IMAGE)\:latest

tag-version: 
	docker tag $(APP_IMAGE) $(APP_IMAGE)\:$(APP_VERSION)

#######################################################################