import scrapy
from scrapy import Request

class MovieidSpider(scrapy.Spider):
    name = 'movieID'
    allowed_domains = ['boxofficemojo.com/','imdb.com/']
    start_urls = ['http://boxofficemojo.com//']

    
    def __init__(self, release=None, **kwargs):
        self.start_urls = [f'https://www.boxofficemojo.com/release/{release}/weekend/']  # py36
        super().__init__(**kwargs)  # python3
        
    def parse(self, response):
        id = response.css(".a-box-inner").css("a::attr(href)").extract_first().split("/")[4]
        yield Request("https://www.imdb.com/title/"+id, callback=self.parse_movie,dont_filter=True)
            
            
    def parse_movie(self, response):
        
        yield {"title": response.xpath("//h1/text()").extract_first()}
           
        
        
