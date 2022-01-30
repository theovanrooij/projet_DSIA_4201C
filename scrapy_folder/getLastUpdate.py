import pymongo

def connectBDD():
    
    client = pymongo.MongoClient("mongo_app")
    database = client['boxoffice']
    return database['scrapy_items']
    
def getLastUpdate():
   
    collection = connectBDD()
    
    cur = list(collection.aggregate([
        {
          "$group": {"_id":{"year":"$year","week":"$week"}}  
        },
        {
            "$sort": {"_id.year":-1,"_id.week":-1}
        }
    ]))
    
    if len(cur) == 0 : 
        return (0,0)
    else :
        return (cur[0]["_id"]["year"], cur[0]["_id"]["week"])
    
def getNewItems():
    collection = connectBDD()
    
    cur = list(collection.aggregate([
        {
          "$match": {"director.name":{"$exists":False}}  
        },
        {
            "$group": {"_id":"$releaseID"}
        }
    ]))
    
    return [movie["_id"] for movie in cur]
