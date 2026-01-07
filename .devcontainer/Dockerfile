FROM python:3.12-slim

# Install uv binary from official image
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# Install system dependencies (git, curl, wget, etc.)
# Done as early as possible to ensure availability
RUN apt-get update && apt-get install -y --no-install-recommends \
    git \
    curl \
    wget \
    procps \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Set working directory to project-specific path
WORKDIR /workspace/forecast

# Enable bytecode compilation for performance
ENV UV_COMPILE_BYTECODE=1

# Set virtual environment location outside the workspace to prevent volume overwrite
ENV UV_PROJECT_ENVIRONMENT=/venv

# Copy dependency definition
COPY pyproject.toml .

# Install dependencies including dev and all extras
RUN uv sync --all-extras --no-install-project

# Ensure the virtual environment is used by default
ENV PATH="/venv/bin:$PATH"
ENV PYTHONPATH="/workspace/forecast/src"

# Default to bash shell
CMD ["bash"]
