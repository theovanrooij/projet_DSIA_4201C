import scrapy
import json
from scrapy import Request
from ..items import IMDBItem
from getLastUpdate import getNewItems

class ImdbSpider(scrapy.Spider):
    name = 'imdb'
    allowed_domains = ['boxofficemojo.com/','imdb.com/']
    custom_settings = {
        'ITEM_PIPELINES' : {
            'boxoffice.pipelines.IMDBPipeline': 100,
            'boxoffice.pipelines.MongoPipelineIMDB': 300,
        }
    }

    
    def  getPersonId(self,url):
        actorId = url
        if actorId != None :
            actorId = actorId.split("/")[2].split("?")[0]
        return actorId
    
    def __init__(self, *args, **kwargs):
        
        
        import pymongo
        client = pymongo.MongoClient("mongo_app")
        database = client['boxoffice']
        collection_box = database['scrapy_items']

        releases_all = getNewItems()
        
        
        
        self.start_urls = ["https://www.boxofficemojo.com/release/"+release+"/weekend/" for release in releases_all]
        
        #self.start_urls = ["https://www.boxofficemojo.com/release/rl3309339905/weekend/"]
        
        super().__init__(**kwargs)  # python3
        
    def parse(self, response):
        id_movie= response.css(".a-box-inner").css("a::attr(href)").extract_first().split("/")[4]
        
        req = Request("https://www.imdb.com/title/"+id_movie+"/?ref_=nv_sr_srsg_0", callback=self.parse_main,dont_filter=True)
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
        req.meta["recettes_totales"] = response.css(".mojo-performance-summary-table :nth-child(2) .money::text").extract_first()
        
       
        
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
        req.meta["recettes_totales"]  = response.meta.get("recettes_totales") 
        #req.meta["synopsis"] = response.css("meta[name='description']::attr(content)").get()
        try :
            req.meta["resume"] = json.loads(response.css("script[type='application/ld+json']::text").extract_first())["description"]
        except KeyError:
            req.meta["resume"] =  response.css('meta[name="description"]::attr(content)').extract_first()
        req.meta["poster"] = response.css(".ipc-media--poster-l>img::attr(src)").extract_first()
        
        mainCast =list()
        
        #for mainActor in  response.css(".StyledComponents__CastItemSummary-sc-y9ygcu-9.hLoKtW>a"):
        for mainActor in  response.css(".StyledComponents__CastItemWrapper-sc-y9ygcu-7.esVIGD"):
            mainCast.append({"name":mainActor.css("::text").extract_first(),"actorId":self.getPersonId(mainActor.css("a::attr(href)").extract_first()) , "img_link":mainActor.css("img::attr(src)").extract_first()})

        req.meta["mainCast"] = mainCast
        
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
        directorName = response.css("#director+table a::text").extract_first()
        directorId =self.getPersonId(response.css("#director+table a::attr(href)").extract_first())
        
        director = {"name":directorName,"directorId":directorId}
        cast = list()
        
        for actor in response.css(".cast_list>tr"):
            

                cast.append({"name":actor.css(".primary_photo+td>a::text").extract_first(), "role" :actor.css(".character>a::text").extract_first(),"img_link":actor.css("img::attr(loadlate)").extract_first(),"actorId":self.getPersonId(actor.css("a::attr(href)").extract_first())
                })
            
        yield IMDBItem(title = response.meta.get("title"),
                        note = response.meta.get("note"),
                        director = director,
                       cast=cast,
                        genres=response.meta.get("genres"),
                        releaseDate=response.meta.get("releaseDate") ,
                        runningTime = response.meta.get("runningTime"),
                        recettes_inter = response.meta.get("recettes_inter"),
                       recettes_totales = response.meta.get("recettes_totales"),
                        budget = response.meta.get("budget"),
                        country_origin = response.meta.get("country_origin"),
                        releaseID  = response.meta.get("releaseID"),
                       resume  = response.meta.get("resume"),
                       poster = response.meta.get("poster"),
                       mainCast = response.meta.get("mainCast")
                      )
           
        
        
