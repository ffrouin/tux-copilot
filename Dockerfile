# -------------------------------------------------------------
# TUX Copilot sandbox image (Debian bookworm)
# -------------------------------------------------------------
FROM debian:bookworm AS base

ENV DEBIAN_FRONTEND=noninteractive

# Install minimal utilities we might need for future tools
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        python3 python3-pip python3-venv \
        bash git ca-certificates curl jq sudo && \
    rm -rf /var/lib/apt/lists/*

# Create a working directory for the copilot to write files
RUN mkdir -p /workdir
VOLUME /workdir

# Set default user (optional – can be overridden by docker run)
ENV USERNAME=tux
ENV UID=1000
ENV GID=1000

# Create user + sudo privileges
RUN groupadd -g ${GID} ${USERNAME} && \
    useradd -m -u ${UID} -g ${GID} -s /bin/bash ${USERNAME} && \
    usermod -aG sudo ${USERNAME} && \
    echo "${USERNAME} ALL=(ALL) NOPASSWD:ALL" > /etc/sudoers.d/${USERNAME} && \
    chmod 0440 /etc/sudoers.d/${USERNAME}

# Switch to tux user for all remaining operations
USER ${USERNAME}:${USERNAME}
WORKDIR /workdir

CMD ["bash"]
