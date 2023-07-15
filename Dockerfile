FROM python:3.11-alpine as deps-export

WORKDIR /app/
ARG PIP_NO_CACHE_DIR=off

RUN pip install poetry==1.5.1
COPY pyproject.toml poetry.lock ./
RUN poetry export --without-hashes -o requirements.txt

FROM python:3.11-alpine as app

WORKDIR /app/
ARG PIP_NO_CACHE_DIR=off

# To match host UID/GID
ARG HOST_UID
ARG HOST_GID
RUN set -eux; \
  addgroup -g $HOST_GID sshpasslog; \
  adduser -u $HOST_UID -G sshpasslog -D sshpasslog
USER sshpasslog

COPY --from=deps-export /app/requirements.txt .
RUN pip install -r requirements.txt

# src/ is to be bind-mounted instead of copied.

ENV PYTHONUNBUFFERED=x
CMD ["python", "-m", "src.main"]
