import scrapy

class StatsMatch(scrapy.Spider):
    name = "Scrap stats"
    start_urls = ["http://www.hltv.org/stats/matches/85435/g2-vs-natus-vincere",]

    def parse(self, response):
        for player in response.xpath('//table[@class="stats-table"]'):
            tr_value = player.xpath('tr')
            yield { 'tr' : tr_value }