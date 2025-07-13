from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.operators.bash import BashOperator
import sys

sys.path.append("/opt/airflow/etl")
from analytics.generate_reports import main as generate_reports
from analytics.papers_translation import main as translate

with DAG(
    dag_id="scrape_arxiv_etl",
    schedule_interval=None,
    catchup=False
) as dag:

    scrape = BashOperator(
        task_id="scrape",
        bash_command="cd /opt/airflow/etl/arxiv_scraper && scrapy crawl arxiv_new",
    )

    translate = PythonOperator(
        task_id="translate",
        python_callable=translate,
    )

    analyze = PythonOperator(
        task_id="analytics",
        python_callable=generate_reports,
    )

    scrape >> translate >> analyze
