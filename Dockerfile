FROM docker.io/library/python:3.7-slim AS base

RUN apt update -y && python3 -m pip install --upgrade pip

WORKDIR /app

FROM base AS production

COPY LICENSE README.md pyproject.toml ./
COPY aiocli ./aiocli/

RUN python3 -m pip install .

ENTRYPOINT ["python3"]
CMD []

FROM production AS development

COPY .pre-commit-config.yaml run-script ./

RUN python3 -m pip install .[dev,deploy,docs,fmt,security-analysis,static-analysis,test]

COPY docs_src ./docs_src
COPY tests ./tests

ENTRYPOINT ["python3", "run-script"]
