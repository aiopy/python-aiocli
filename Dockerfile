FROM docker.io/library/python:3.6.15-slim as development

WORKDIR /app

COPY .pre-commit-config.yaml LICENSE pyproject.toml pyscript.sh README.md requirements.txt requirements-dev.txt setup.py ./
COPY aiocli ./aiocli/
COPY tests ./tests/

RUN sh pyscript.sh install

ENTRYPOINT ["sh", "pyscript.sh"]
CMD []
