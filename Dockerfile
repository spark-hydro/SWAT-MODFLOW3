# SWAT-MODFLOW3 in a container: build with CMake + gfortran, run a model from a mounted folder.
# The image holds two builds of the program: a fast Release build (default) and a Debug build
# (array-bounds checks, about 3x slower) that is used when the container is started with -e DEBUG=1.
#
#   docker build -t swatmf3 --build-arg VERSION=$(git describe --tags --always) .
#   docker run --rm swatmf3 --version
#   docker run --rm -v /path/to/model:/model swatmf3                  # runs the model in /path/to/model
#   docker run --rm -e DEBUG=1 -v /path/to/model:/model swatmf3       # same, with the debug build
#
# The Docker idea comes from a contribution by Paul van Genuchten (@pvgenuchten), PR #6.

# ---- stage 1: build both versions ----
FROM ubuntu:24.04 AS build
RUN apt-get update \
 && DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends \
      gfortran cmake ninja-build \
 && rm -rf /var/lib/apt/lists/*
WORKDIR /src
COPY CMakeLists.txt .
COPY src ./src
# the git tag is not available inside the image (.git is not copied): pass it in
ARG VERSION=unknown
RUN cmake -S . -B /build-release -G Ninja -D CMAKE_BUILD_TYPE=Release -D TAG="${VERSION}" \
 && cmake --build /build-release \
 && cp "$(find /build-release -maxdepth 1 -type f -name 'swatmf3-*')" /swatmf3-release
# debug: bounds checking, but no floating-point traps (they stop on harmless errors)
RUN cmake -S . -B /build-debug -G Ninja -D CMAKE_BUILD_TYPE=Debug -D SWATMF_FPE_TRAP=OFF -D TAG="${VERSION}" \
 && cmake --build /build-debug \
 && cp "$(find /build-debug -maxdepth 1 -type f -name 'swatmf3-*')" /swatmf3-debug

# ---- stage 2: small runtime image ----
FROM ubuntu:24.04
LABEL org.opencontainers.image.source="https://github.com/spark-hydro/SWAT-MODFLOW3"
LABEL org.opencontainers.image.description="SWAT-MODFLOW3: SWAT2012 coupled with MODFLOW-NWT and RT3D"
COPY --from=build /swatmf3-release /usr/local/bin/swatmf3-release
COPY --from=build /swatmf3-debug /usr/local/bin/swatmf3-debug
COPY docker/entrypoint.sh /usr/local/bin/swatmf3
# the model folder (with file.cio and swatmf_link.txt) is mounted here
WORKDIR /model
ENTRYPOINT ["swatmf3"]
