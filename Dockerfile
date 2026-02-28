FROM python:3.12-slim

WORKDIR /app

# Install uv
RUN pip install uv --no-cache-dir

# Copy project files
COPY pyproject.toml uv.lock ./
COPY src/ ./src/

# Install dependencies
RUN uv sync --frozen --no-dev

# Expose port
EXPOSE 8080

# Run the HTTP server
CMD ["uv", "run", "commune-mcp-http"]
