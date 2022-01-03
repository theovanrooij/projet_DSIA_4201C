import scrapy


class HtlvSpider(scrapy.Spider):
    name = 'htlv'
    allowed_domains = ['hltv.org/']
    start_urls = ["http://www.hltv.org/stats/matches/85435/g2-vs-natus-vincere",]

    def parse(self, response):
        teams = []
        for i,table in enumerate(response.xpath('//table[@class="stats-table"]')):
            team = table.xpath('.//thead/tr/th/text()').extract_first()
            teams.append(team)
        
        for i,table in enumerate(response.xpath('//table[@class="stats-table"]')):
            for player in table.xpath('.//tbody/tr'):
                playerName = player.xpath('.//td[@class="st-player"]//a/text()').extract_first()
                nationality = player.xpath('.//td[@class="st-player"]').css('img::attr(alt)').extract_first()
                
                yield { 'team' : teams[i],"opponent":teams[i-1],"player":playerName,"nationality":nationality }
            