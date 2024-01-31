"""A spider for movies data from wikipedia."""
import json
from typing import Any

import scrapy
from itemloaders.processors import MapCompose
from scrapy.crawler import CrawlerProcess
from scrapy.http import Request, Response
from scrapy.loader import ItemLoader

from movies_scraper.items import MovieItem


def process_value(value: str) -> str | None:
    """
    Check if the string is empty and strip it.

    Args:
        value: The string value to check.
    """
    stripped_value = value.strip()
    if not stripped_value:
        return None
    return stripped_value


class MoviesSpider(scrapy.Spider):
    """
    Spider for crawling movie data from Wikipedia and IMDb.
    """
    name = "movies"
    allowed_domains = ["ru.wikipedia.org", "imdb.com"]
    start_urls = ["https://ru.wikipedia.org/wiki/Категория:Фильмы_по_алфавиту"]

    custom_settings = {
        'FEED_FORMAT': 'csv',
        'FEED_URI': 'movies.csv',
    }

    headers = {
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        'Accept-Encoding': 'gzip, deflate, br',
        'Accept-Language': 'en-US,en;q=0.9',
        'Connection': 'keep-alive',
        'Host': 'www.imdb.com',
        'Sec-Fetch-Dest': 'document',
        'Sec-Fetch-Mode': 'navigate',
        'Sec-Fetch-Site': 'none',
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) '
                      'AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2.1 Safari/605.1.15',
    }

    def parse(self, response: Response, **kwargs: Any):
        """
        The default callback used by Scrapy to process downloaded responses.

        Args:
            response: The response object to parse.
        """
        for movie_link in response.xpath("//div[@id='mw-pages']//li/a/@href").extract():
            yield Request(url=response.urljoin(movie_link), callback=self.parse_movie_page)

        next_page = response.xpath(
            "//a[contains(text(),'Следующая страница')]/@href").extract_first()

        if next_page:
            yield Request(url=response.urljoin(next_page), callback=self.parse)

    def parse_movie_page(self, response: Response):
        """
        Parses individual movie pages on Wikipedia to extract movie data.

        Args:
            response: The response object to parse.
        """
        loader = ItemLoader(item=MovieItem(), response=response)
        loader.add_xpath('title',
                         "//*[@id=\"firstHeading\"]/descendant-or-self::*/text()")
        loader.add_xpath('genre',
                         "//span[@data-wikidata-property-id='P136']//text()|"
                         "//div[@data-wikidata-property-id='P136']//text()",
                         MapCompose(process_value),
                         re=r"^[А-Яа-яЁёA-Za-z][.А-Яа-яЁёA-Za-z,/ '’-]+$")
        loader.add_xpath('director',
                         "//span[@data-wikidata-property-id='P57']//text()|"
                         "//div[@data-wikidata-property-id='P57']//text()",
                         MapCompose(process_value),
                         re=r"^[А-Яа-яЁёA-Za-z-][А-Яа-яЁёA-Za-z,'’\s-]+$|"
                            r"^[А-Яа-яЁёA-Za-z’\s-]+\.?\s[А-Яа-яЁёA-Za-z'’\s-]+$")
        loader.add_xpath('country',
                         "//span[@data-wikidata-property-id='P495']/descendant-or-self::*/text()",
                         MapCompose(process_value),
                         re=r'^[А-Яа-яЁё][А-Яа-яЁё\s]+$')
        loader.add_xpath('year',
                         "//span[@class='dtstart']/text()|"
                         "//span[@data-wikidata-property-id='P577']//a/text()|"
                         "//th[contains(text(),'Год')]/following-sibling::td//text()|"
                         "//span[@data-wikidata-property-id='P580']//a/text()",
                         re=r'\d{4}')

        imdb_url = response.xpath("//span[@data-wikidata-property-id='P345']//a/@href").get()

        if imdb_url:
            yield Request(url=imdb_url,
                          headers=self.headers,
                          callback=self.parse_imdb_page,
                          meta={'loader': loader})
        else:
            yield loader.load_item()

    def parse_imdb_page(self, response: Response):
        """
        Parses individual IMDb pages to extract the movie's rating.

        Args:
            response: The response object to parse.
        """
        loader = response.meta['loader']
        json_data = response.xpath("//script[@type='application/ld+json']/text()").get()

        if json_data:
            data = json.loads(json_data)

            aggregate_rating = data.get("aggregateRating", {}).get("ratingValue")

            if aggregate_rating:
                loader.add_value('imdb_rating', aggregate_rating)
        return loader.load_item()


def main():
    """
    The main entry point for running the spider.
    """
    process = CrawlerProcess()
    process.crawl(MoviesSpider)
    process.start()


if __name__ == "__main__":
    main()
