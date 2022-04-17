FROM docker.io/library/python:3.6.15-slim AS production

WORKDIR /app

COPY LICENSE pyproject.toml pyscript.sh README.md requirements.txt setup.py ./

RUN apt update -y && python3 -m pip install --upgrade pip

COPY aiocli ./aiocli/

ENTRYPOINT ["sh", "pyscript.sh"]
CMD []

FROM production AS development

COPY .pre-commit-config.yaml requirements-dev.txt ./

RUN sh pyscript.sh install

COPY docs ./docs
COPY docs_src ./docs_src
COPY tests ./tests
