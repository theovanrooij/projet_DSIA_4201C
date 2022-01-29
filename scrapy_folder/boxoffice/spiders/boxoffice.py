import scrapy
from scrapy import Request
from ..items import BoxofficeItem
from getLastUpdate import getLastUpdate


class BoxOfficeSpider(scrapy.Spider):
    name = 'boxoffice'
    allowed_domains = ['boxofficemojo.com/']
    custom_settings = {
            'ITEM_PIPELINES' : {
                'boxoffice.pipelines.BoxofficePipeline': 100,
                'boxoffice.pipelines.MongoPipeline': 300,
            }
        }
    
    
    def __init__(self, year=2007, **kwargs):
        # importing date class from datetime module
        from datetime import date

        # creating the date object of today's date
        current_year = date.today().year
        
        self.start_urls = []
        
        lastYear,lastWeek = getLastUpdate()
        
        self.lastYear = lastYear
        self.lastWeek = lastWeek
        
        
        for year in range(self.lastYear,current_year+1):
            self.start_urls.append(f'https://www.boxofficemojo.com/weekend/by-year/{year}/?area=FR')  # py36
      
        super().__init__(**kwargs)  # python3
        
        
    def parse(self, response):
        all_links = []
        year = response.css("h1.mojo-gutter::text").extract_first().split(" ")[-1]
        for interval in response.xpath('//td[contains(@class, "mojo-field-type-date_interval") and contains(@class, "a-text-left")]') :
            link = interval.css('a::attr(href)').extract_first()
            weekYear = link.split("/")[2].split("W")
            if ( int(weekYear[0]) >= self.lastYear and  int(weekYear[1])> self.lastWeek ):
                all_links.append(link)
        
        for link in all_links:
            req = Request("https://www.boxofficemojo.com"+link, callback=self.parse_weekend,dont_filter=True)
            req.meta["year"] = year
            yield req
            
            
    def parse_weekend(self, response):
        
        week = response.xpath('//h1[@class="mojo-gutter"]/text()').extract_first()
           
        for i,tr in enumerate(response.xpath('//table/tr')):
             if i != 0 :
                    datas = tr.xpath('.//text()').extract()
                    if  datas[3][0] != "$":
                        datas[2] += " "+datas.pop(3)
                    releaseID = tr.css('a::attr(href)').extract_first().split("/")[2]
                    yield BoxofficeItem( 
                        year = response.meta.get("year"),
                        week= week[len(week)-2:],
                        rank=datas[0],
                        rank_last_week=datas[1],
                        title=datas[2],
                        recettes=datas[3],
                        boxDiff=datas[4],
                        recettes_cumul=datas[8],
                        nbCinemas=datas[5],
                        cinemasDiff=datas[6],
                        nbWeeks=datas[9],
                        distributor=datas[10],
                        releaseID = releaseID
                    )
                    