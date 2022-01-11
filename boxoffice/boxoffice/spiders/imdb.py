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
        
        
        import pymongo
        client = pymongo.MongoClient("mongo_app")
        database = client['boxoffice']
        collection_box = database['scrapy_items']

        releases_all = list(collection_box.distinct("releaseID"))
        
        self.start_urls = ["https://www.boxofficemojo.com/release/"+release+"/weekend/" for release in releases_all]
        
        #self.start_urls = ["https://www.boxofficemojo.com/release/rl1023116289/weekend/"]
        
        super().__init__(**kwargs)  # python3
        
    def parse(self, response):
        id_movie= response.css(".a-box-inner").css("a::attr(href)").extract_first().split("/")[4]
        
        req = Request("https://www.imdb.com/title/"+id_movie, callback=self.parse_main,dont_filter=True)
        req.meta["movieID"] = id_movie
        req.meta["releaseID"]  = response.request.url.split("/")[4]
        
        
        div = response.css(".mojo-summary-values .a-section")
        for subdiv in div :
            content = subdiv.css("span ::text").extract()
            if content[0] == "Genres":
                req.meta["genres"] =content[1]
            if content[0] in ["Release Date","Earliest Release Date"]:
                req.meta["releaseDate"] =content[1]
            if content[0] == "Running Time":
                
                req.meta["runningTime"] =content[1]
        
        req.meta["recettes_inter"] = response.css(".mojo-performance-summary-table :nth-child(4) .money::text").extract_first()
        
       
        
        yield req
            
    def parse_main(self, response):
        req = Request("https://www.imdb.com/title/"+response.meta.get("movieID")+"/fullcredits", 
                      callback=self.parse_credits,dont_filter=True)
        req.meta["note"] = response.css(".AggregateRatingButton__RatingScore-sc-1ll29m0-1::text").extract_first()
        req.meta["title"]=response.css("h1::text").extract_first()
        req.meta["releaseID"]  = response.meta.get("releaseID") 
        req.meta["releaseDate"]  = response.meta.get("releaseDate") 
        req.meta["genres"]  = response.meta.get("genres") 
        req.meta["runningTime"]  = response.meta.get("runningTime") 
        req.meta["recettes_inter"]  = response.meta.get("recettes_inter") 
        
        
        for item in  response.css(".ipc-metadata-list__item"):
            content = item.css("::text").extract()
            if content[0] == "Country of origin":
                req.meta["country_origin"] = content[1]
        
        budget = response.css(".BoxOffice__MetaDataListItemBoxOffice-sc-40s2pl-2:nth-child(1) ::text").extract()
        if len(budget)>=2:
            req.meta["budget"]  = budget[1]
        else : 
            req.meta["budget"] = None
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
                       cast = cast,
                       genres=response.meta.get("genres"),
                       releaseDate=response.meta.get("releaseDate") ,
                       runningTime = response.meta.get("runningTime"),
                       recettes_inter = response.meta.get("recettes_inter"),
                       budget = response.meta.get("budget"),
                       country_origin = response.meta.get("country_origin"),
                         releaseID  = response.meta.get("releaseID"))
           
        
        
