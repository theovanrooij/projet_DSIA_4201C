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
        
        item["rank_last_week"] = self.checkNA(item["rank_last_week"])
        
        item["nbCinemas"] = self.checkNA(item["nbCinemas"])
        
        item["cinemasDiff"] = self.checkNA(item["cinemasDiff"])
        
        item["boxDiff"] = self.checkNA(item["boxDiff"],True)
        
        if item["distributor"] == "-" :
            
            item["distributor"] = "Inconnu"
        
        item["boxoffice"] = self.clean_money(item["boxoffice"])
        item["boxoffice_cumul"] = self.clean_money(item["boxoffice_cumul"])
        
        return item

    def checkNA(self,value,percent=False):
        if value != "-" :
            if percent :
                return float(value.rstrip('%').lstrip("+"))
            else:
                return int(value.replace(",",""))
        else:
            return np.NaN
        
    def clean_money(self,money):
        return int(money.replace("$","").replace(",",""))
        
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

class IMDBPipeline:
    def process_item(self, item, spider):
        
        new_cast = dict()
        old_cast = item["cast"]
        
        for actor in old_cast.keys():
            if actor != None :
                new_cast[self.clean_name(actor)] = old_cast[actor]
                        
        item["cast"] = new_cast
        
        item["director"] = self.clean_name(item["director"])
        
        item["note"] = float(item["note"])
        
        return item

   
        
    def clean_name(self,name):
        return name.lstrip(" ").rstrip("\n")
    
class MongoPipelineIMDB(object):

    collection_name = 'imdb_items'

    def open_spider(self, spider):
        self.client = pymongo.MongoClient("mongo_app")
        self.db = self.client["imdb"]
        self.db[self.collection_name].delete_many({})

    def close_spider(self, spider):
        self.client.close()

    def process_item(self, item, spider):
        self.db[self.collection_name].insert(dict(item),check_keys=False)
        return item