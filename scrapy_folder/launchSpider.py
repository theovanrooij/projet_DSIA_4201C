import os.path
from time import sleep




# Regarde si le fichier contenant le nombre de documents voulu existe. 
while not os.path.isfile("/home/mongo_data/nb.txt"):
    print("Does not exist")
    sleep(1)

# Regarde si le fichier contenant le nombre de documents voulu existe. 
with open('/home/mongo_data/nb.txt') as f:
    nbDocumentsVoulu = f.readlines()

import pymongo
client = pymongo.MongoClient("mongo_app")
database = client['boxoffice']
collection = database['scrapy_items']


# #La base de données ne s'est pas mise à jour avec la dernière vcersion disponible
while int(nbDocumentsVoulu[0]) > collection.count_documents({}) :
    print("Database is restoring")
    sleep(5)
    


from boxoffice.spiders.imdb import ImdbSpider
from boxoffice.spiders.boxoffice import BoxOfficeSpider

from twisted.internet import reactor, defer
from scrapy.crawler import CrawlerRunner
from scrapy.utils.log import configure_logging


@defer.inlineCallbacks
def crawl():
    yield runner.crawl(BoxOfficeSpider)
    yield runner.crawl(ImdbSpider)
    reactor.stop()

configure_logging()
runner = CrawlerRunner()
crawl()
reactor.run() # the script will block here until the last crawl call is finished