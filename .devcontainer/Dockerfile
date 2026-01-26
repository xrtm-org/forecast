FROM python:3.12-slim

# Install uv binary from official image
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# Install system dependencies
# Added zsh and robust terminal tools
RUN apt-get update && apt-get install -y --no-install-recommends \
    git \
    curl \
    wget \
    procps \
    ca-certificates \
    zsh \
    zsh-autosuggestions \
    zsh-syntax-highlighting \
    && rm -rf /var/lib/apt/lists/*

# Install GitHub CLI
RUN curl -fsSL https://cli.github.com/packages/githubcli-archive-keyring.gpg | dd of=/usr/share/keyrings/githubcli-archive-keyring.gpg \
    && chmod go+r /usr/share/keyrings/githubcli-archive-keyring.gpg \
    && echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/githubcli-archive-keyring.gpg] https://cli.github.com/packages stable main" | tee /etc/apt/sources.list.d/github-cli.list > /dev/null \
    && apt-get update \
    && apt-get install -y gh \
    && rm -rf /var/lib/apt/lists/*

# Configure Zsh (assuming root user)
RUN echo 'export PS1="%F{green}%n@%m%f:%F{blue}%~%f$ "' >> /root/.zshrc \
    && echo 'source /usr/share/zsh-autosuggestions/zsh-autosuggestions.zsh' >> /root/.zshrc \
    && echo 'source /usr/share/zsh-syntax-highlighting/zsh-syntax-highlighting.zsh' >> /root/.zshrc \
    && echo 'bindkey "^[[A" history-beginning-search-backward' >> /root/.zshrc \
    && echo 'bindkey "^[[B" history-beginning-search-forward' >> /root/.zshrc \
    && echo 'alias ls="ls --color=auto"' >> /root/.zshrc \
    && echo 'alias grep="grep --color=auto"' >> /root/.zshrc \
    && echo 'zstyle ":completion:*" menu select' >> /root/.zshrc \
    && echo 'autoload -Uz compinit && compinit' >> /root/.zshrc

# Set working directory to project-specific path
WORKDIR /workspace/forecast

# Enable bytecode compilation for performance
ENV UV_COMPILE_BYTECODE=1

# Set virtual environment location outside the workspace to prevent volume overwrite
ENV UV_PROJECT_ENVIRONMENT=/venv

# Copy dependency definition
COPY forecast/pyproject.toml .
# Also need to copy siblings' pyproject.toml for uv resolution if it's going to check them
# But we'll try just the main one first. uv might need the paths to exist.
RUN mkdir -p ../data ../eval ../train
COPY data/pyproject.toml ../data/
COPY eval/pyproject.toml ../eval/
COPY train/pyproject.toml ../train/

# Install dependencies including dev (skipping heavy extras like vllm/llama-cpp)
# We skip this during image build because local path dependencies (../data, etc) 
# are only available at runtime via mounts.
# RUN uv sync --no-install-project --extra dev

# Ensure the virtual environment is used by default
ENV PATH="/venv/bin:$PATH"
ENV PYTHONPATH="/workspace/forecast/src"

# Default to zsh shell
CMD ["zsh"]
