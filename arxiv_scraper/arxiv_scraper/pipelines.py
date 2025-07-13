import psycopg2
from arxiv_scraper.settings import DB_CONFIG

class PostgreSQLPipeline:

    def open_spider(self, spider):
        self.conn = psycopg2.connect(**DB_CONFIG)
        self.cur = self.conn.cursor()
        self.cur.execute("""
            CREATE TABLE IF NOT EXISTS arxiv_papers (
                arxiv_id TEXT PRIMARY KEY,
                title TEXT,
                authors TEXT,
                abstract TEXT,
                abstract_translation TEXT,
                word_count INTEGER,
                primary_subject TEXT,
                paper_url TEXT,
                pdf_url TEXT,
                is_translated BOOLEAN
            )
        """)
        self.conn.commit()

    def process_item(self, item, spider):
        abstract = item.get("abstract", "")
        item["word_count"] = len(abstract.split()) if abstract else 0
        item["is_translated"] = False
        authors_str = ", ".join(item.get("authors", []))

        self.cur.execute("""
            INSERT INTO arxiv_papers (
                arxiv_id, title, authors, abstract, abstract_translation,
                word_count, primary_subject, paper_url, pdf_url, is_translated
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (arxiv_id) DO NOTHING
        """, (
            item["arxiv_id"],
            item["title"],
            authors_str,
            item["abstract"],
            item.get("abstract_translation"),  # usually None
            item["word_count"],
            item["primary_subject"],
            item["paper_url"],
            item["pdf_url"],
            item["is_translated"]
        ))
        self.conn.commit()
        return item

    def close_spider(self, spider):
        self.cur.close()
        self.conn.close()
