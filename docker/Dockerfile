# Use the official Python 3.13 image
FROM astral/uv:python3.13-bookworm

# Setup a non-root user
RUN groupadd --system --gid 999 nonroot \
    && useradd --system --gid 999 --uid 999 --create-home nonroot

# Install the project into `/app`
WORKDIR /app

# Environment variables for UV
ENV UV_COMPILE_BYTECODE=1
ENV UV_LINK_MODE=copy
ENV UV_TOOL_BIN_DIR=/usr/local/bin

# Install dependencies first (for better caching)
# Mount from parent directory since Dockerfile is in docker/ folder
RUN --mount=type=cache,target=/root/.cache/uv \
    --mount=type=bind,source=../uv.lock,target=uv.lock \
    --mount=type=bind,source=../pyproject.toml,target=pyproject.toml \
    uv sync --locked --no-install-project --no-dev

# Copy the entire project root (parent of docker folder) to /app
COPY .. /app

# Install the project itself
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --locked --no-dev

# Set up the environment
ENV PATH="/app/.venv/bin:$PATH"
ENTRYPOINT []
USER nonroot

EXPOSE 8000

# Start FastAPI from root, so Python can access configs etc.
CMD ["fastapi", "run", "src/main.py", "--host", "0.0.0.0", "--port", "8000", "--workers", "2", "--proxy-headers"]