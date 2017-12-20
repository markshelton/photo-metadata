BUILD_CONTEXT = ./src/
DOCKERIGNORE_PATH = ./src/config/.dockerignore
DOCKERFILE_PATH = ./src/config/Dockerfile
PROJECT_DIR = $(shell echo $(CURDIR) | sed 's|^/[^/]*||')

CONFIG ?= ./src/config/config.env
include $(CONFIG)
export $(shell sed 's/=.*//' $(CONFIG))

APP_NAME = "$(REPO_NAME)/$(PROJECT_NAME)"

.DEFAULT_GOAL := build

# Main
up: build run
shell:
	docker exec -it $(PROJECT_NAME) /bin/bash
browser:
	explorer.exe "http://localhost:8888"
stop:
	docker stop $(PROJECT_NAME)
publish: repo-login publish-latest publish-version
tag: tag-latest tag-version

# Helpers
build: prebuild; docker build -t $(PROJECT_NAME) -f $(DOCKERFILE_PATH) $(BUILD_CONTEXT)
build-nc: prebuild; docker build --no-cache -t $(PROJECT_NAME) -f $(DOCKERFILE_PATH) $(BUILD_CONTEXT)
run: 
	docker run -td --rm --name="$(PROJECT_NAME)" \
		-p 8888:8888 -p 6006:6006 \
		-v $(PROJECT_DIR)/data:/home/app/data \
		$(PROJECT_NAME)
publish-latest: 
	docker push $(APP_NAME)\:latest
publish-version: 
	docker push $(APP_NAME)\:$(VERSION)
prebuild:
	npm list -g dockerignore --depth=0 || npm install -g dockerignore
	dockerignore -g=".gitignore" -D="$(DOCKERIGNORE_PATH)"
repo-login: 
	docker login -u $(REPO_NAME)
tag-latest: 
	docker tag $(PROJECT_NAME) $(APP_NAME)\:latest
tag-version: 
	docker tag $(PROJECT_NAME) $(APP_NAME)\:$(VERSION)
version:
	@echo $(VERSION)