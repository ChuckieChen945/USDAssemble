# syntax=docker/dockerfile:1
FROM ghcr.io/astral-sh/uv:python3.12-bookworm AS dev

# Create and activate a virtual environment [1].
# [1] https://docs.astral.sh/uv/concepts/projects/config/#project-environment-path
ENV VIRTUAL_ENV=/opt/venv
ENV PATH=$VIRTUAL_ENV/bin:$PATH
ENV UV_PROJECT_ENVIRONMENT=$VIRTUAL_ENV

# Tell Git that the workspace is safe to avoid 'detected dubious ownership in repository' warnings.
RUN git config --system --add safe.directory '*'

# Create a non-root user and give it passwordless sudo access [1].
# [1] https://code.visualstudio.com/remote/advancedcontainers/add-nonroot-user
RUN --mount=type=cache,target=/var/cache/apt/ \
    --mount=type=cache,target=/var/lib/apt/ \
    groupadd --gid 1000 user && \
    useradd --create-home --no-log-init --gid 1000 --uid 1000 --shell /usr/bin/bash user && \
    chown user:user /opt/ && \
    apt-get update && apt-get install --no-install-recommends --yes sudo && \
    echo 'user ALL=(root) NOPASSWD:ALL' > /etc/sudoers.d/user && chmod 0440 /etc/sudoers.d/user
USER user

# Configure the non-root user's shell.
RUN mkdir ~/.history/ && \
    echo 'HISTFILE=~/.history/.bash_history' >> ~/.bashrc && \
    echo 'bind "\"\e[A\": history-search-backward"' >> ~/.bashrc && \
    echo 'bind "\"\e[B\": history-search-forward"' >> ~/.bashrc && \
    echo 'eval "$(starship init bash)"' >> ~/.bashrc

FROM python:3.12-slim AS app

# Configure Python to print tracebacks on crash [1], and to not buffer stdout and stderr [2].
# [1] https://docs.python.org/3/using/cmdline.html#envvar-PYTHONFAULTHANDLER
# [2] https://docs.python.org/3/using/cmdline.html#envvar-PYTHONUNBUFFERED
ENV PYTHONFAULTHANDLER=1
ENV PYTHONUNBUFFERED=1

# Remove docker-clean so we can manage the apt cache with the Docker build cache.
RUN rm /etc/apt/apt.conf.d/docker-clean

# Install compilers that may be required for certain packages or platforms.
RUN --mount=type=cache,target=/var/cache/apt/ \
    --mount=type=cache,target=/var/lib/apt/ \
    apt-get update && \
    apt-get install --no-install-recommends --yes build-essential

# Create a non-root user and switch to it [1].
# [1] https://code.visualstudio.com/remote/advancedcontainers/add-nonroot-user
RUN groupadd --gid 1000 user && \
    useradd --create-home --no-log-init --gid 1000 --uid 1000 user
USER user

# Set the working directory.
WORKDIR /workspaces/usdassemble/

# Copy the app source code to the working directory.
COPY --chown=user:user . .

# Install the application and its dependencies [1].
# [1] https://docs.astral.sh/uv/guides/integration/docker/#optimizations
RUN --mount=type=cache,uid=1000,gid=1000,target=/home/user/.cache/uv \
    --mount=from=ghcr.io/astral-sh/uv,source=/uv,target=/bin/uv \
    uv sync \
    --all-extras \
    --compile-bytecode \
    --frozen \
    --link-mode copy \
    --no-dev \
    --no-editable \
    --python-preference only-system

# Expose the app.
ENTRYPOINT ["/workspaces/usdassemble/.venv/bin/usdassemble"]
CMD []
