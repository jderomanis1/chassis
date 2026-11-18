FROM ghcr.io/astral-sh/uv:0.13.9 AS uv
FROM python:3.12-slim-bookworm
COPY --from=uv /uv /usr/local/bin/uv
RUN apt-get update && apt-get install -y --no-install-recommends git tzdata \
    && rm -rf /var/lib/apt/lists/* \
    && useradd --create-home --shell /bin/bash demo \
    && install -d -m 0700 -o demo -g demo /home/demo/.ssh /run/chassis-demo /var/data \
    && ln -s /var/data/current /run/chassis-demo/current
WORKDIR /app
COPY pyproject.toml uv.lock ./
COPY src/ src/
RUN uv sync --locked --no-dev --extra portal --no-editable && uv cache clean
COPY deploy/door.py deploy/start.py deploy/meeting.py /app/deploy/
ENV PATH="/app/.venv/bin:${PATH}" PYTHONUNBUFFERED=1
USER demo
CMD ["/app/.venv/bin/python", "/app/deploy/start.py"]
