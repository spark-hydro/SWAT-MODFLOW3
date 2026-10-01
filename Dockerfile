# SWAT-MODFLOW3 in a container: build with CMake + gfortran, run a model from a mounted folder.
#
#   docker build -t swatmf3 --build-arg VERSION=$(git describe --tags --always) .
#   docker run --rm swatmf3 --version
#   docker run --rm -v /path/to/model:/model swatmf3     # runs the model in /path/to/model
#
# The Docker idea comes from a contribution by Paul van Genuchten (@pvgenuchten), PR #6.

# ---- stage 1: build ----
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
RUN cmake -S . -B /build -G Ninja -D CMAKE_BUILD_TYPE=Release -D TAG="${VERSION}" \
 && cmake --build /build \
 && cp "$(find /build -maxdepth 1 -type f -name 'swatmf3-*')" /swatmf3

# ---- stage 2: small runtime image ----
FROM ubuntu:24.04
LABEL org.opencontainers.image.source="https://github.com/spark-hydro/SWAT-MODFLOW3"
LABEL org.opencontainers.image.description="SWAT-MODFLOW3: SWAT2012 coupled with MODFLOW-NWT and RT3D"
COPY --from=build /swatmf3 /usr/local/bin/swatmf3
# the model folder (with file.cio and swatmf_link.txt) is mounted here
WORKDIR /model
ENTRYPOINT ["swatmf3"]
