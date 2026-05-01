FROM python:3.14-slim

COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

WORKDIR /opt/grafana-backup-tool

COPY pyproject.toml ./
COPY uv.lock ./ 

RUN uv sync --frozen --no-install-project

COPY . .

RUN uv sync --frozen

RUN mkdir -p _OUTPUT_

ENV RESTORE=false \
    ARCHIVE_FILE="" \
    GRAFANA_URL="http://localhost:3000"

ENV PATH="/opt/grafana-backup-tool/.venv/bin:$PATH"

ENTRYPOINT ["grafana-backup"]
CMD ["save"]