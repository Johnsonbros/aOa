# LSP Comparison Server
# Provides pyright for fair aOa vs LSP benchmarking

FROM python:3.11-slim

# Install Node.js for pyright
RUN apt-get update && \
    apt-get install -y curl && \
    curl -fsSL https://deb.nodesource.com/setup_20.x | bash - && \
    apt-get install -y nodejs jq && \
    rm -rf /var/lib/apt/lists/*

# Install pyright (Python LSP)
RUN npm install -g pyright

# Install pylsp as alternative
RUN pip install python-lsp-server jedi

WORKDIR /workspace

# Healthcheck
HEALTHCHECK --interval=10s --timeout=3s \
    CMD pyright --version || exit 1

# Keep running for exec commands
CMD ["tail", "-f", "/dev/null"]
