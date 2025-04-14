FROM python:3.11-alpine AS base
ARG HOST_UID HOST_GID
RUN \
  addgroup -g $HOST_GID user \
  && adduser -D -u $HOST_UID -G user user
USER user
ENV \
  PATH=/home/user/.local/bin:/usr/local/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin \
  PIP_DISABLE_PIP_VERSION_CHECK=true \
  VIRTUAL_ENV=/home/user/venv
WORKDIR /app/

FROM base AS poetry_export
RUN pip install --user --no-cache-dir "poetry-plugin-export==1.9.*"
COPY pyproject.toml poetry.lock ./
RUN poetry export --without=dev --without-hashes -o /home/user/requirements.txt

FROM base AS deps
RUN \
  pip install --user --no-cache-dir virtualenv \
  && virtualenv $VIRTUAL_ENV
COPY --from=poetry_export /home/user/requirements.txt /home/user/requirements.txt
RUN \
    --mount=type=cache,target=/home/user/.cache/,uid=$HOST_UID,gid=$HOST_GID \
  source $VIRTUAL_ENV/bin/activate && \
  pip install -r /home/user/requirements.txt

FROM base AS app
ENV PATH=$VIRTUAL_ENV/bin:"$PATH"
COPY --from=deps $VIRTUAL_ENV $VIRTUAL_ENV
# src/ is to be bind-mounted instead of copied.
ENV PYTHONUNBUFFERED=x
CMD ["python", "-m", "src.main"]
