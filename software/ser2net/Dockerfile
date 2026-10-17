# Pin base image and primary package. Security dependencies remain Debian-managed.
FROM debian:bookworm-slim@sha256:7c7b2c966bc9ee8cedfeef67e0e279108992c77681fa595db4a9d65c06ccc587
RUN apt-get update \
    && apt-get install --no-install-recommends -y ser2net=4.3.11-1 \
    && rm -rf /var/lib/apt/lists/*
ENTRYPOINT ["/usr/sbin/ser2net", "-n", "-c", "/etc/ser2net.yaml", "-P", "/tmp/ser2net.pid"]
