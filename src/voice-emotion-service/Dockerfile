FROM python:3.12-slim
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

ENV UV_LINK_MODE=copy
ENV UV_PYTHON_CACHE_DIR=/root/.cache/uv/python
ENV UV_PYTHON_VERSION=3.13

RUN apt-get update && apt-get install -y --no-install-recommends \
    libsndfile1 \
    ffmpeg \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app/infer

COPY common/pyproject.toml /app/common/
COPY infer/pyproject.toml infer/uv.lock /app/infer/

RUN --mount=type=cache,target=/root/.cache/uv,sharing=locked \
    uv sync --frozen --no-install-project

COPY common/ /app/common/
COPY infer/ /app/infer/

RUN --mount=type=cache,target=/root/.cache/uv,sharing=locked \
    uv sync --locked

COPY train/out/model.pth /etc/
CMD ["/app/infer/.venv/bin/fastapi", "run", "main.py", "--port", "42069", "--host", "0.0.0.0"]

