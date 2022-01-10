import scrapy
from scrapy import Request
from ..items import IMDBItem

class ImdbSpider(scrapy.Spider):
    name = 'imdb'
    allowed_domains = ['boxofficemojo.com/','imdb.com/']
    custom_settings = {
        'ITEM_PIPELINES' : {
            'boxoffice.pipelines.IMDBPipeline': 100,
            'boxoffice.pipelines.MongoPipelineIMDB': 300,
        }
    }

    
    def __init__(self, *args, **kwargs):
        
        realise_list = kwargs.get('releases_args').split(',')
        self.start_urls = ["https://www.boxofficemojo.com/release/"+release+"/weekend/" for release in realise_list]
    
        super().__init__(**kwargs)  # python3
        
    def parse(self, response):
        
        id_movie= response.css(".a-box-inner").css("a::attr(href)").extract_first().split("/")[4]
        req = Request("https://www.imdb.com/title/"+id_movie, callback=self.parse_main,dont_filter=True)
        req.meta["movieID"] = id_movie
        yield req
            
    def parse_main(self, response):
        req = Request("https://www.imdb.com/title/"+response.meta.get("movieID")+"/fullcredits", 
                      callback=self.parse_credits,dont_filter=True)
        req.meta["note"] = response.css(".AggregateRatingButton__RatingScore-sc-1ll29m0-1::text").extract_first()
        req.meta["title"]=response.css("h1::text").extract_first()
        
        yield req
        
    def parse_credits(self, response):
        director = response.css("#director+table a::text").extract_first()
        cast = dict()
        
        #for actor in response.xpath('//table[contains(@class, "cast_list")]//tbody//tr'):
        for actor in response.css(".cast_list>tr"):
            cast[actor.css(".primary_photo+td>a::text").extract_first()] = [actor.css(".character>a::text").extract_first(),actor.css("img::attr(src)").extract_first()]
            
        yield IMDBItem(title = response.meta.get("title"),
                       note = response.meta.get("note"),
                       director = director,
                       cast = cast)
           
        
        
