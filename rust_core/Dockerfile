FROM rust:latest as builder

WORKDIR /usr/src/concord-rust-core
# Install CMake (needed for rdkafka)
RUN apt-get update && apt-get install -y cmake

COPY rust_core .

# Build release binary
ENV PYO3_USE_ABI3_FORWARD_COMPATIBILITY=1
RUN cargo build --release

FROM debian:bookworm-slim
COPY --from=builder /usr/src/concord-rust-core/target/release/libconcord_rust_core.so /usr/local/lib/
# If we were building an executable service:
# COPY --from=builder /usr/src/concord-rust-core/target/release/concord-service /usr/local/bin/

# For this demo, we'll keep the container alive to simulate a service
CMD ["tail", "-f", "/dev/null"]
