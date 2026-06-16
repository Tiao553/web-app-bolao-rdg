FROM python:3.12-slim

WORKDIR /app

RUN pip install --no-cache-dir uv

COPY pyproject.toml ./
RUN uv pip install --system --no-cache -e ".[dev]" 2>/dev/null || \
    uv pip install --system --no-cache \
        fastapi uvicorn[standard] sqlalchemy alembic \
        psycopg[binary] pydantic pydantic-settings httpx PyYAML \
        python-multipart playwright resend

RUN python -m playwright install --with-deps chromium

COPY . .

EXPOSE 8000

CMD ["sh", "start.sh"]
