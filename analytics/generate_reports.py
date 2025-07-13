import os

import polars as pl
import matplotlib.pyplot as plt

from helpers.db_config import get_connection
from dotenv import load_dotenv
load_dotenv()


def main():
    conn = get_connection()
    df = extract(conn)
    generate_reports(df)

def extract(conn) -> pl.DataFrame:
    query = """
        SELECT arxiv_id, primary_subject, word_count
        FROM arxiv_papers
    """
    try:
        df = pl.read_database(query, conn)
        return df
    finally:
        conn.close()


def generate_reports(df: pl.DataFrame, output_dir='plots'):
    os.makedirs(output_dir, exist_ok=True)
    subject_counts_pl = df.group_by("primary_subject").agg(
        pl.len().alias("count_of_articles")
    )
    subject_counts_pl = subject_counts_pl.sort("count_of_articles", descending=True)

    subject_counts_pd = subject_counts_pl.to_pandas()

    plt.figure(figsize=(12, 7))
    plt.bar(subject_counts_pd["primary_subject"], subject_counts_pd["count_of_articles"], color="skyblue")
    plt.xlabel("Primary Subject")
    plt.ylabel("Number of Articles")
    plt.title("Number of Articles per Primary Subject")
    plt.xticks(rotation=45, ha="right")
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, "articles_per_subject.png"))
    plt.close()

    avg_word_count_pl = df.group_by("primary_subject").agg(
        pl.col("word_count").mean().alias("avg_word_count")
    )
    avg_word_count_pl = avg_word_count_pl.sort("avg_word_count", descending=True)
    avg_word_count_pd = avg_word_count_pl.to_pandas()

    plt.figure(figsize=(12, 7))
    plt.bar(avg_word_count_pd["primary_subject"], avg_word_count_pd["avg_word_count"], color="lightcoral")
    plt.xlabel("Primary Subject")
    plt.ylabel("Average Word Count")
    plt.title("Average Word Count per Primary Subject")
    plt.xticks(rotation=45, ha="right")
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, "avg_word_count_per_subject.png"))
    plt.close()
