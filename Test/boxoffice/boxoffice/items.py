# Define here the models for your scraped items
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/items.html

import scrapy


class BoxofficeItem(scrapy.Item):
    # define the fields for your item here like:
    # name = scrapy.Field()
    
    week = scrapy.Field()
    rank = scrapy.Field()
    rank_last_week = scrapy.Field()
    movie = scrapy.Field()
    boxoffice = scrapy.Field()
    boxDiff = scrapy.Field()
    boxoffice_cumul = scrapy.Field()
    nbCinemas = scrapy.Field()
    cinemasDiff = scrapy.Field()
    nbWeeks = scrapy.Field()
    distributor = scrapy.Field()
    releaseID = scrapy.Field()


