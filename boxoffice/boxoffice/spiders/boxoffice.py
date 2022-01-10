import scrapy
from scrapy import Request
from ..items import BoxofficeItem

class BoxOfficeSpider(scrapy.Spider):
    name = 'boxoffice'
    allowed_domains = ['boxofficemojo.com/']
    custom_settings = {
            'ITEM_PIPELINES' : {
                'boxoffice.pipelines.BoxofficePipeline': 100,
                'boxoffice.pipelines.MongoPipeline': 300,
            }
        }

    def __init__(self, year=2021, **kwargs):
        self.start_urls = [f'https://www.boxofficemojo.com/weekend/by-year/{year}/?area=FR']  # py36
        super().__init__(**kwargs)  # python3
        
        
    def parse(self, response):
        all_links = []
        weeks = []
        
        for interval in response.xpath('//td[contains(@class, "mojo-field-type-date_interval") and contains(@class, "a-text-left")]') :
            all_links.append(interval.css('a::attr(href)').extract_first())
            
        for link in all_links:
            yield Request("https://www.boxofficemojo.com"+link, callback=self.parse_weekend,dont_filter=True)
            
            
    def parse_weekend(self, response):
        
        week = response.xpath('//h1[@class="mojo-gutter"]/text()').extract_first()
           
        for i,tr in enumerate(response.xpath('//table/tr')):
             if i != 0 :
                    datas = tr.xpath('.//text()').extract()
                    releaseID = tr.css('a::attr(href)').extract_first().split("/")[2]
                    yield BoxofficeItem( 
                        week= week[len(week)-2:],
                        rank=datas[0],
                        rank_last_week=datas[1],
                        movie=datas[2],
                        boxoffice=datas[3],
                        boxDiff=datas[4],
                        boxoffice_cumul=datas[8],
                        nbCinemas=datas[5],
                        cinemasDiff=datas[6],
                        nbWeeks=datas[9],
                        distributor=datas[10],
                        releaseID = releaseID
                    )
                    