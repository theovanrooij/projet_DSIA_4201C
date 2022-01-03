# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://docs.scrapy.org/en/latest/topics/item-pipeline.html


# useful for handling different item types with a single interface
from itemadapter import ItemAdapter

import numpy as np

class BoxofficePipeline:
    def process_item(self, item, spider):
        
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
                return int(value)
        else:
            return np.NaN
        
    def clean_money(self,money):
        return int(money.replace("$","").replace(",",""))
        
import pymongo

class MongoPipeline(object):

    collection_name = 'scrapy_items'

    def open_spider(self, spider):
        self.client = pymongo.MongoClient("mongo")
        self.db = self.client["boxoffice"]
        self.db[self.collection_name].delete_many({})

    def close_spider(self, spider):
        self.client.close()

    def process_item(self, item, spider):
        self.db[self.collection_name].insert_one(dict(item))
        return item