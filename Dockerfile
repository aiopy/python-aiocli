FROM docker.io/library/python:3.7-slim AS production

WORKDIR /app

COPY LICENSE README.md pyproject.toml ./

RUN apt update -y &&  \
    python3 -m pip install --upgrade pip && \
    python3 -m pip install .

COPY aiocli ./aiocli/

ENTRYPOINT ["python3"]
CMD []

FROM production AS development

RUN apt install -y gcc

COPY .pre-commit-config.yaml run-script ./

RUN python3 run-script dev-install

COPY docs ./docs
COPY tests ./tests

ENTRYPOINT ["python3", "run-script"]
