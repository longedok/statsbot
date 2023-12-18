FROM python:3.11-alpine AS base

ENV PIP_DISABLE_PIP_VERSION_CHECK=on \
    PYTHONUNBUFFERED=1

WORKDIR /app
RUN mkdir /data

FROM base as builder

RUN apk --no-cache add curl gcc musl-dev libffi-dev
ENV POETRY_VIRTUALENVS_CREATE=false \
   POETRY_HOME='/usr/local' \
   POETRY_VERSION='1.7.1'

RUN curl -sSL 'https://install.python-poetry.org' | python3 && poetry --version
RUN python -m venv /venv

COPY poetry.lock pyproject.toml /app/
RUN . /venv/bin/activate && poetry install --no-dev --no-root

COPY . /app

FROM base as final

COPY --from=builder /venv /venv
COPY . /app

