# Define here the models for your scraped items
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/items.html

import scrapy


class BoxofficeItem(scrapy.Item):
    # define the fields for your item here like:
    # name = scrapy.Field()
    year = scrapy.Field()
    week = scrapy.Field()
    week_year = scrapy.Field()
    rank = scrapy.Field()
    rank_last_week = scrapy.Field()
    title = scrapy.Field()
    recettes = scrapy.Field()
    boxDiff = scrapy.Field()
    recettes_cumul = scrapy.Field()
    nbCinemas = scrapy.Field()
    cinemasDiff = scrapy.Field()
    nbWeeks = scrapy.Field()
    distributor = scrapy.Field()
    releaseID = scrapy.Field()
    


class IMDBItem(scrapy.Item):

    title = scrapy.Field()
    note = scrapy.Field()
    director = scrapy.Field()
    cast = scrapy.Field()
    releaseID = scrapy.Field()
    runningTime =scrapy.Field()
    releaseDate =scrapy.Field()
    genres = scrapy.Field()
    recettes_inter = scrapy.Field()
    budget  =  scrapy.Field()
    country_origin =   scrapy.Field()
    synopsis  = scrapy.Field()
    poster  = scrapy.Field()
    mainCast = scrapy.Field()
    