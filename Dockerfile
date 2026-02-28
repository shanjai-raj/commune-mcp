FROM python:3.12-slim

WORKDIR /app

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

# Copy project files
COPY pyproject.toml uv.lock ./
COPY src/ ./src/

# Install dependencies (no --frozen: resolves for Linux platform)
RUN uv sync --no-dev --no-cache

# Expose port
EXPOSE 8080

# Run the HTTP server
CMD ["uv", "run", "commune-mcp-http"]
