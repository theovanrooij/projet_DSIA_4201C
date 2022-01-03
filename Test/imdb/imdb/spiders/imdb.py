import scrapy


class BoxSpider(scrapy.Spider):
    name = 'imdb'
    allowed_domains = ['imdb.com/']
    start_urls = ['http://imdb.com//']

    def parse(self, response):
        pass
