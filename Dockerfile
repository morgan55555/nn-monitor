# From lite debian image
FROM debian:trixie-slim

# Define build arguments for the UID/GID with default values
ARG USER_NAME=runner
ARG USER_UID=1001
ARG USER_GID=1001

# Install required packages
RUN --mount=target=/var/lib/apt/lists,type=cache,sharing=locked \
    --mount=target=/var/cache/apt,type=cache,sharing=locked \
    rm -f /etc/apt/apt.conf.d/docker-clean \
    && apt-get update \
    && apt-get -y --no-install-recommends install \
        git python3

# Create the group and user
RUN groupadd --gid $USER_GID $USER_NAME && \
    useradd --uid $USER_UID --gid $USER_GID -m $USER_NAME -s /bin/bash

# Set the working directory to the new user's home directory
WORKDIR /home/${USER_NAME}

# Copy application files and set ownership
COPY --chown=$USER_UID:$USER_GID ./res .

# Switch to the non-root user
USER $USER_NAME

# Install python dependencies
RUN --mount=type=cache,target=/root/.cache/pip pip install --no-cache-dir -r requirements.txt && \
    pip install --no-cache-dir -r https://raw.githubusercontent.com/mathoudebine/turing-smart-screen-python/refs/heads/main/requirements.txt

# Clone repo
RUN git clone https://github.com/mathoudebine/turing-smart-screen-python.git

# Run with python
ENTRYPOINT ["python3", "nn-monitor.py"]