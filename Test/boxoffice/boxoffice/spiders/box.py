import scrapy


class BoxSpider(scrapy.Spider):
    name = 'box'
    allowed_domains = ['boxofficemojo.com/']
    start_urls = ["https://www.boxofficemojo.com/weekend/2019W25/?area=FR&ref_=bo_wey_table_44",]

    def parse(self, response):
        week = response.xpath('//h1[@class="mojo-gutter"]/text()').extract_first()
        
        #for tr in response.xpath('//table/*//text()'):
            
           # yield { "week": week[len(week)-2:],"table":tr.extract()}
           
        for i,tr in enumerate(response.xpath('//table/tr')):
             if i != 0 :
                    datas = tr.xpath('.//text()').extract()
                    
                    yield { "week": week[len(week)-2:],"rank":datas[0],"rank_last_week":datas[1],
                           "movie":datas[2],"boxoffice":datas[3],"boxDiff":datas[4],"boxoffice_cumul":datas[8],"nbCinemas":datas[5],"cinemasDiff":datas[6],"nbWeeks":datas[9],"distributor":datas[10]}
        