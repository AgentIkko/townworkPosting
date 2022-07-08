import scrapy
from scrapy.linkextractors import LinkExtractor
from scrapy.spiders import CrawlSpider, Rule
from townwork.items import TownworkItem
import datetime, re

salaryReHour = re.compile(r"時給(.+?)円")
salaryReMonth = re.compile(r"月給(.+?)円")

def getSalary(salaryStr):

    resHour = re.search(salaryReHour,salaryStr)
    resMonth = re.search(salaryReMonth,salaryStr)
    salaryNmHour, salaryNmMonth = None, None

    if resHour:
        salaryNmHour = resHour.group(1)
    if resMonth:
        salaryNmMonth = resMonth.group(1)

    return salaryNmHour, salaryNmMonth


class KeywordsindeedSpider(scrapy.Spider):
    
    name = 'townwork'
    allowed_domains = ['townwork.net']
    
    def start_requests(self):

        start_urls = [
            "https://townwork.net/joSrchRsltList/?emc=01&emc=06&sac=55202&jmc=01501&jmc=01520",
                     ]
        # 20 records/page
        for p in list(range(2,6)):
            start_urls.append(f'https://townwork.net/joSrchRsltList/?emc=01&emc=06&sac=55202&jmc=01501&jmc=01520&page={p}')
            #start_urls.append(f'https://townwork.net/joSrchRsltList/?ac=042&jc=012&page={p}')
            #start_urls.append(f'https://townwork.net/joSrchRsltList/?ac=043&jc=012&page={p}')
            #start_urls.append(f'https://townwork.net/joSrchRsltList/?ac=044&jc=012&page={p}')
        
        for url in start_urls:
            
            yield scrapy.Request(url=url, callback=self.parse)
        



    
        
    def parse(self, response):
        
        cards = response.xpath('//div[@class="job-lst-main-cassette-wrap"]')
        
        for card in cards:
            
            item = TownworkItem()
            
            detailedUrl =  'https://townwork.net' + card.xpath('.//div[@class="job-lst-box-wrap"]/a').attrib['href']
            
            
            """ 枠マスター原稿用

                        
            yield scrapy.Request(detailedUrl,
                                 callback=self.parse_detail,
                                 meta={'item':item})
            """            
            
            """ 一般用 """
            
            #if "joid_U" in detailedUrl:# 枠原稿飛ばす。少なすぎる
            #    continue
                
            item['today'] = datetime.date.today()
            
            try:# 新着案件用、でないとtimelimitないやつ取れない。逆に掲載終了案件欲しいときはつけないと量が膨大？
                item['timelimit'] = "掲載終了：" + card.xpath('.//p[@class="job-lst-main-period-limit"]/span/text()').get()
            except Exception:
                item['timelimit'] = "None"
                
            salaryText = card.xpath('.//table/tbody/tr[1]/td//text()').extract()
            salaryText = "".join([e.strip() for e in salaryText])
            item['salary'] = salaryText
            nmH, nmM = getSalary(salaryText)
            item["salaryNumHour"] = nmH
            item["salaryNumMonth"] = nmM
            
            stationText = card.xpath('.//table/tbody/tr[2]/td//text()').extract()
            item['station'] = "".join([e.strip() for e in stationText])
            
            wtText = card.xpath('.//table/tbody/tr[3]/td//text()').extract()
            item['workingtime'] = "".join([e.strip() for e in wtText])
            
            item['url'] = detailedUrl
                        
            yield scrapy.Request(detailedUrl,
                                 callback=self.parse_detail,
                                 meta={'item':item})

            
    
    def parse_detail(self,response):
        
        item = response.meta['item']
        
        """ 枠マスター原稿用

        item['company'] = response.xpath('.//span[@class="jsc-company-txt"]/text()').get().strip()
        item['title'] = response.xpath('.//span[@class="jsc-job-txt"]/text()').get().strip()
        item['catch'] = response.xpath('.//div[@class="job-detail-caption-c"]/text()').extract()
        item['lead'] = response.xpath('.//dl[@class="job-ditail-tbl-inner"]/dt[contains(text(),"アピール情報")]/following-sibling::dd//text()').extract()
        """
        
        """ 一般用 """
        
        item['company'] = response.xpath('.//span[@class="jsc-company-txt"]/text()').get().strip()
        
        item['occupation'] = response.xpath('.//span[@class="jsc-job-txt"]/text()').get().strip()
        item['title'] = response.xpath('.//div[@class="job-detail-caption-c"]/text()').get()
        # item['subtitle'] = response.xpath('.//p[@class="job-detail-txt"]/text()').get()
        
        loc = response.xpath('.//dl[@class="job-ditail-tbl-inner"]/dt[contains(text(),"勤務地")]/following-sibling::dd//text()').extract()
            
        item['location'] = " ".join([l.strip() for l in loc])

        telNum = response.xpath('.//p[@class="detail-tel-num"]/span/text()').get()
        if telNum == None:
            telNumPre = response.xpath('.//p[@class="detail-tel-ttl"]/span/text()').extract()
            telNum = [t.strip() for t in telNumPre if len(t.strip()) > 0][0]
        
        item['tel'] = telNum

        yield item
