FROM docker.io/continuumio/miniconda3:latest AS miniconda3

WORKDIR /app

RUN conda install -y --download-only "python=3.12" && \
    conda install -y --download-only "python=3.11" && \
    conda install -y --download-only "python=3.10" && \
    conda install -y --download-only "python=3.9"

COPY . ./

ENTRYPOINT ["python3"]
CMD ["run-script"]

FROM miniconda3 AS py312

RUN conda install -y "python=3.12"
RUN --mount=type=cache,target=/root/.cache/pip python3 run-script dev-install

FROM miniconda3 AS py311

RUN conda install -y "python=3.11"
RUN --mount=type=cache,target=/root/.cache/pip python3 run-script dev-install

FROM miniconda3 AS py310

RUN conda install -y "python=3.10"
RUN --mount=type=cache,target=/root/.cache/pip python3 run-script dev-install

FROM miniconda3 AS py39

RUN conda install -y "python=3.9"
RUN --mount=type=cache,target=/root/.cache/pip python3 run-script dev-install
