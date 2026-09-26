# ============================================================
# Stage 1 — Builder (instala dependências com uv)
# ============================================================
FROM ghcr.io/astral-sh/uv:python3.12-bookworm-slim AS builder

ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    UV_PYTHON_DOWNLOADS=0

WORKDIR /app

# Copiar arquivos de dependência primeiro (melhor cache de layers)
COPY pyproject.toml uv.lock /app/

# Instalar dependências (cache de deps separado do código)
# Inclui dev group (pytest, pytest-django, etc.) — venv do container já vem
# com tudo pra rodar a suite sem pip install manual.
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-install-project

# ============================================================
# Stage 2 — Runtime (imagem slim, sem uv)
# ============================================================
FROM python:3.12-slim-bookworm

ENV PYTHONUNBUFFERED=1 \
    VIRTUAL_ENV=/app/.venv \
    PATH="/app/.venv/bin:$PATH"

EXPOSE 8080

WORKDIR /src

# 1. Criar um grupo e um usuário de sistema sem privilégios (UID/GID padrão 1000)
RUN addgroup --system --gid 1000 appgroup \
    && adduser --system --uid 1000 --ingroup appgroup appuser \
    && apt-get update \
    && apt-get install -y --no-install-recommends curl ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# curl pra healthcheck/diagnostico do proprio service em runtime
# Copiar venv do builder
COPY --from=builder /app/.venv /app/.venv

# Copiar código
COPY src /src/

# 2. Ajustar o ownership dos diretórios que a aplicação precisa acessar
# e garantir bit de execucao do entrypoint
RUN chown -R appuser:appgroup /src /app/.venv \
    && chmod +x /src/start_service.sh

# 3. Trocar para o usuário non-root ANTES de rodar a aplicação
USER appuser

# Entrypoint default: migra, collectstatic e sobe gunicorn (ver script).
CMD ["./start_service.sh"]