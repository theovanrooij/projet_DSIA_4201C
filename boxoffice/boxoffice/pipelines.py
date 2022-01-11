# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://docs.scrapy.org/en/latest/topics/item-pipeline.html


# useful for handling different item types with a single interface
from itemadapter import ItemAdapter

import numpy as np

class BoxofficePipeline:
    def process_item(self, item, spider):
        item["year"]  = int(item["year"])
        item["rank"] = int(item["rank"])
        item["week"] = int(item["week"])
        item["nbWeeks"] = int(item["nbWeeks"])
        
        item["rank_last_week"] = checkNA(item["rank_last_week"])
        
        item["nbCinemas"] = checkNA(item["nbCinemas"])
        
        item["cinemasDiff"] = checkNA(item["cinemasDiff"])
        
        item["boxDiff"] = checkNA(item["boxDiff"],True)
        
        if item["distributor"] == "-" :
            
            item["distributor"] = "Inconnu"
        
        item["recettes"] = clean_money(item["recettes"])
        item["recettes_cumul"] = clean_money(item["recettes_cumul"])
        
        return item

def checkNA(value,percent=False):
    if value not in ["-",None] :
        if percent :
            return float(value.rstrip('%').lstrip("+"))
        else:
            return int(value.replace(",",""))
    else:
        return np.NaN
        
def clean_money(money):
    if money[0] == "€" :
        
        multiplicateur = 1.13
        
    else : 
        multiplicateur = 1
    return int(multiplicateur * int(money.split(" ")[0].replace("$","").replace(",","").replace("€","")))
        
import pymongo

class MongoPipeline(object):

    collection_name = 'scrapy_items'

    def open_spider(self, spider):
        self.client = pymongo.MongoClient("mongo_app")
        self.db = self.client["boxoffice"]
        self.db[self.collection_name].delete_many({})

    def close_spider(self, spider):
        self.client.close()

    def process_item(self, item, spider):
        self.db[self.collection_name].insert_one(dict(item))
        return item
    
    
    
#### IMDB ITEMS
def checkNone(value):
    if value not in [None] :
        return float(value)
    else : 
        return np.NaN
    
class IMDBPipeline:
    def process_item(self, item, spider):
        
        new_cast = dict()
        old_cast = item["cast"]
        
        for actor in old_cast.keys():
            if actor != None :
                new_cast[self.clean_name(actor)] = old_cast[actor]
                        
        item["cast"] = new_cast
        
        item["director"] = self.clean_name(item["director"])
        
        item["note"] = checkNone(item["note"])
        
        if item["runningTime"] != None :
            time = item["runningTime"].replace(" ","").split("hr")
            if len(time)>=2 :
                hour = time[0]
                mins = time[1].split("min")[0]
                if mins =="":
                    mins=0
                item["runningTime"] = int(time[0])*60+int(mins)
            else :
                item["runningTime"] = time[0].replace("min","")
        else:
            item["runningTime"] = np.NaN
    
        if item["genres"] != None :
            item["genres"]= [genre for genre in item["genres"].replace(" ","").split("\n") if genre]

        item["recettes_inter"] = clean_money(item["recettes_inter"])
         
        if item["budget"] == None :
            item["budget"] = np.NaN
        
        return item

   
        
    def clean_name(self,name):
        if name != None:
            return name.lstrip(" ").rstrip("\n")
        else : return name
    
class MongoPipelineIMDB(object):

    collection_name = 'scrapy_items'

    def open_spider(self, spider):
        self.client = pymongo.MongoClient("mongo_app")
        self.db = self.client["boxoffice"]

    def close_spider(self, spider):
        self.client.close()

    def process_item(self, item, spider):
        print(item["releaseID"])
        self.db[self.collection_name].update_many(
    {
        "releaseID": item["releaseID"] },
        {
            "$set":  dict(item) 
        }
)
        #self.db[self.collection_name].insert(dict(item),check_keys=False)
        return item