FROM apache/airflow:2.9.1-python3.11

USER root

RUN apt-get update && apt-get install -y \
    curl \
    libpq-dev \
    build-essential \
    && apt-get clean

RUN curl -sSL https://install.python-poetry.org | python3 - && \
    ln -s /root/.local/bin/poetry /usr/local/bin/poetry

WORKDIR /opt/airflow/etl

COPY pyproject.toml poetry.lock /opt/airflow/etl/

RUN poetry config virtualenvs.create false && poetry install --no-root

WORKDIR /opt/airflow

COPY dags /opt/airflow/dags
COPY analytics /opt/airflow/etl/analytics
COPY arxiv_scraper /opt/airflow/etl/arxiv_scraper
COPY helpers /opt/airflow/etl/helpers
COPY logs /opt/airflow/logs
COPY plugins /opt/airflow/plugins

USER airflow
