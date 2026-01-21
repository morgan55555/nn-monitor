# From lite debian image
FROM debian:trixie-slim

# Install required packages
RUN --mount=target=/var/lib/apt/lists,type=cache,sharing=locked \
    --mount=target=/var/cache/apt,type=cache,sharing=locked \
    rm -f /etc/apt/apt.conf.d/docker-clean \
    && apt-get update \
    && apt-get -y --no-install-recommends install \
        git python3 python3-pip lm-sensors

# Set the working directory
WORKDIR /nn-monitor

# Copy application files and set ownership
COPY ./res .

# Install python dependencies
RUN --mount=type=cache,target=/root/.cache/pip \
    pip config set global.break-system-packages true \
    && pip install --no-cache-dir -r requirements.txt \
    && pip install --no-cache-dir -r https://raw.githubusercontent.com/mathoudebine/turing-smart-screen-python/refs/heads/main/requirements.txt

# Clone repo
RUN git clone https://github.com/mathoudebine/turing-smart-screen-python.git

# Run with python
ENTRYPOINT ["python3", "nn-monitor.py"]