# Pin base image and primary package. Security dependencies remain Debian-managed.
FROM debian:bookworm-slim@sha256:734a72b3d6142a71993b4bc580ca01d8ca687f77a2c422d96a961d3376b179bc
RUN apt-get update \
    && apt-get install --no-install-recommends -y ser2net=4.3.11-1 \
    && rm -rf /var/lib/apt/lists/*
ENTRYPOINT ["/usr/sbin/ser2net", "-n", "-c", "/etc/ser2net.yaml", "-P", "/tmp/ser2net.pid"]
