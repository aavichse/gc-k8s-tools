IMAGE_NAME := arikab64/gc-labels-lab
DOCKERFILE := Dockerfile
TAG := 1.0

.PHONY: all
all: build


.PHONY: build
build:
	docker build -t $(IMAGE_NAME):$(TAG) -f $(DOCKERFILE) .

.PHONY: run
run:
	docker run --rm -v $(PWD):/app $(IMAGE_NAME):$(TAG) -f config.yaml

# Push the Docker image to a registry
.PHONY: push
push:
	docker push $(IMAGE_NAME):$(TAG)

# Clean up local Docker images
.PHONY: clean
clean:
	docker rmi $(IMAGE_NAME):$(TAG)

# Help target to display usage information
.PHONY: help
help:
	@echo "Makefile Targets:"
	@echo "  build   - Build the Docker image"
	@echo "  run     - Run the container with a mounted config file (default: config.yaml)"
	@echo "  push    - Push the Docker image to a container registry"
	@echo "  clean   - Remove the local Docker image"
	@echo "  help    - Display this help message"
