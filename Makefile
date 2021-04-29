IMAGE_COMMON=harbor.jiangxingai.com/library/
#IMAGE_COMMON=registry.jiangxingai.com:5000/
APP_NAME=app-w2s-asp
VER=$(shell cat ./VERSION)

PLATA32=arm32v7
PLATA64=arm64v8
PLATX64=x8664

BUILD_A32=linux/arm/v7
BUILD_A64=linux/arm64v8
BUILD_X64=linux/amd64

GO=CGO_ENABLED=0 go

.PHONY: create destroy build push save

create:
	export DOCKER_CLI_EXPERIMENTAL=enabled && docker buildx create --use --name trueno_builder --config ./buildkitd.toml
	export DOCKER_CLI_EXPERIMENTAL=enabled && docker buildx inspect trueno_builder --bootstrap

destroy:
	export DOCKER_CLI_EXPERIMENTAL=enabled && docker buildx rm trueno_builder

build:
	echo $(DOCKERFILE)
	export DOCKER_CLI_EXPERIMENTAL=enabled && docker buildx version
	export DOCKER_CLI_EXPERIMENTAL=enabled && docker buildx build -t $(IMAGE_FULL)  --platform=$(BUILD_PLAT) -o type=docker -f $(DOCKERFILE) .

push:
	docker push $(IMAGE_FULL)

save:
	docker save $(IMAGE_FULL) > $(APP_NAME)_$(PLAT)_$(VER).tar.gz

#build_arm: Dockerfile.arm64v8
#	mkdir pack && cd pack && wget http://10.53.3.11:8080/file/grpcio-1.27.2-cp36-cp36m-linux_aarch64.whl  && wget http://10.53.3.11:8080/file/grpcio_tools-1.27.2-cp36-cp36m-linux_aarch64.whl && wget http://10.53.3.11:8080/file/numpy-1.16.1-cp36-cp36m-linux_aarch64.whl && cd ..
#	docker build -t $(NODE_IMAGE) -f $< .
#	rm -r pack
#build_x86: Dockerfile.x8664
#	docker build -t $(CLUSTER_X86_IMAGE) -f $< .
#push_x86: build_x86
#	docker push $(CLUSTER_X86_IMAGE)

x86: PLAT=$(PLATX64)
x86: BUILD_PLAT=$(BUILD_X64)
x86: IMAGE_FULL=$(IMAGE_COMMON)$(APP_NAME)/$(PLAT)/others:$(VER)
x86: DOCKERFILE=Dockerfile.x8664
x86: build push

arm: PLAT=$(PLATA64)
arm: BUILD_PLAT=$(BUILD_A64)
arm: IMAGE_FULL=$(IMAGE_COMMON)$(APP_NAME)/$(PLAT)/others:$(VER)
arm: DOCKERFILE=Dockerfile.arm64v8
arm: build push

armv7: PLAT=$(PLATA32)
armv7: BUILD_PLAT=$(BUILD_A32)
armv7: IMAGE_FULL=$(IMAGE_COMMON)$(APP_NAME)/$(PLAT)/others:$(VER)
armv7: DOCKERFILE=Dockerfile.arm32v7
armv7: build push