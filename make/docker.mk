#
# docker makefile
#

.PHONY: build rebuld push detox-push docker-run docker-clean
 
$(if $(DOCKER_REGISTRY),,$(error DOCKER_REGISTRY is undefined))
registry=$(DOCKER_REGISTRY)

exec = chamber exec $(PROFILE) --

image = $(registry)/$(project)

base_version = $(shell release -J -r seven-testnet latest)

build_opts := --tag $(image) --progress plain

Dockerfile: VERSION
	sed -i Dockerfile -e "s/^FROM [^/]*\/seven-base:.*\$$/FROM $(registry)\/seven-base:$(base_version)/"

### build image
build: release requirements.txt Dockerfile
	#rm -rf docker/dist
	#mkdir -p docker/dist
	#$(foreach wheel,common client videogen_client,cp dist/seven_$(wheel)*.whl docker/dist; )
	docker build $(build_opts) .
	docker tag $(image):latest $(image):$(version)

### rebuild image
rebuild:
	$(MAKE) build_opts="$(build_opts) --no-cache" build

### push image to docker registry
push: build
	docker push $(image):latest
	docker push $(image):$(version)

### make push with tox disabled
detox-push:
	$(MAKE) DISABLE_TOX=1 push

### run standalone container image for dev/test
docker-run: 
	$(exec) docker run --rm -it $(image)

docker-clean:
	rm -rf docker/dist
