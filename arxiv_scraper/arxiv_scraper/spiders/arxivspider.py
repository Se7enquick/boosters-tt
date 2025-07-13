import scrapy

class ArxivNewSpider(scrapy.Spider):
    name = "arxiv_new"
    allowed_domains = ["arxiv.org"]
    start_urls = ["https://arxiv.org/list/cs.AI/new?skip=0&show=2000"]

    def parse(self, response):
        dts = response.css("dl > dt")
        dds = response.css("dl > dd")

        for dt, dd in zip(dts, dds):
            arxiv_id = dt.css('a[title="Abstract"]::attr(id)').get()
            if not arxiv_id:
                self.logger.warning("Missing arxiv_id, skipping item")
                continue

            href = dt.css("a::attr(href)").get()
            if not href:
                self.logger.warning(f"Missing href for arxiv_id {arxiv_id}, skipping item")
                continue
            paper_url = response.urljoin(href)

            title_raw = dd.css("div.list-title.mathjax::text").getall()
            if not title_raw:
                self.logger.warning(f"Missing title for arxiv_id {arxiv_id}")
                title = "Unknown"
            else:
                title = " ".join([t.strip() for t in title_raw]).replace("Title:", "").strip()

            authors = dd.css("div.list-authors a::text").getall()
            if not authors:
                self.logger.info(f"No authors found for arxiv_id {arxiv_id}")

            abstract_parts = dd.css("p.mathjax::text").getall()
            if not abstract_parts:
                self.logger.info(f"No abstract found for arxiv_id {arxiv_id}")
            abstract = " ".join([a.strip() for a in abstract_parts])

            primary_subject = dd.css("span.primary-subject::text").get()
            if not primary_subject:
                primary_subject = "Unknown"

            pdf_url = paper_url.replace("/abs/", "/pdf/") + ".pdf"

            yield {
                "arxiv_id": arxiv_id,
                "title": title,
                "authors": authors,
                "abstract": abstract,
                "primary_subject": primary_subject,
                "paper_url": paper_url,
                "pdf_url": pdf_url,
            }