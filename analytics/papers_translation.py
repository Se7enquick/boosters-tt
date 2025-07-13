import time
import os
from helpers.logger import get_logger
from helpers.db_config import get_connection
from psycopg2.extras import execute_values
import requests
from dotenv import load_dotenv
load_dotenv()

DEEPL_API_URL = os.getenv('DEEPL_API_URL')
DEEPL_API_KEY = os.getenv('DEEPL_API_KEY')
TARGET_LANG = "UK"
BATCH_SIZE = 50
MAX_RETRIES = 3
RETRY_DELAY_SEC = 5

logging = get_logger(__name__)

def translate_batch(texts):
    """
    Translate a batch of texts synchronously with DeepL API.
    Retry on failures.
    """
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            data = []
            for t in texts:
                data.append(("text", t))
            data.append(("target_lang", TARGET_LANG))
            data.append(("auth_key", DEEPL_API_KEY))

            response = requests.post(DEEPL_API_URL, data=data, timeout=30)
            response.raise_for_status()
            result = response.json()
            return [trans["text"] for trans in result["translations"]]
        except Exception as e:
            logging.warning(f"DeepL API call failed on attempt {attempt}: {e}")
            if attempt < MAX_RETRIES:
                time.sleep(RETRY_DELAY_SEC)
            else:
                raise
    return []

def fetch_untranslated_rows(conn, batch_size):
    """
    Fetch batch of rows where is_translated IS False.
    """
    with conn.cursor() as cur:
        cur.execute(
            f"""
            SELECT arxiv_id, abstract
            FROM arxiv_papers
            WHERE is_translated IS False
            LIMIT %s
            """,
            (batch_size,)
        )
        return cur.fetchall()

def update_translations(conn, rows_with_translations):
    """
    Bulk update abstract_translation in DB.
    rows_with_translations: list of tuples (arxiv_id, translated_text)
    """
    with conn.cursor() as cur:
        query = """
            UPDATE arxiv_papers AS t
            SET abstract_translation = data.translated_text,
                is_translated = True
            FROM (VALUES %s) AS data(id, translated_text)
            WHERE t.arxiv_id = data.id
        """
        execute_values(cur, query, rows_with_translations)
    conn.commit()

def main():
    logging.info("Starting translation batch job...")
    conn = get_connection()

    try:
        while True:
            rows = fetch_untranslated_rows(conn, BATCH_SIZE)
            if not rows:
                logging.info("No more untranslated rows found. Exiting.")
                break

            ids, texts = zip(*rows)
            logging.info(f"Translating batch of {len(texts)} rows...")
            translated_texts = translate_batch(texts)

            update_data = list(zip(ids, translated_texts))
            update_translations(conn, update_data)

            logging.info(f"Batch translated and updated {len(texts)} rows.")
            time.sleep(1)

    except Exception as e:
        logging.error(f"Fatal error: {e}")
    finally:
        conn.close()
        logging.info("Database connection closed.")