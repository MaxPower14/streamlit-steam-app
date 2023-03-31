import json
from urllib.request import Request
import scrapy
from scrapy.selector import Selector
import urllib   
import requests
from scrapy.crawler import CrawlerProcess
import re

class steamcrawler(scrapy.Spider):
    name = 'steamcrawler'
    start_urls = ['https://store.steampowered.com/search/results/?query&start=0&count=50&dynamic_data=&force_infinite=1&category1=998&specials=1&snr=1_7_7_2300_7&infinite=1']
    custom_settings = {
        'LOG_ENABLED': False,
    }
    def parse(self, response):
        #Tomamos la primera respuesta para obtener el total de resultados
        data = dict(response.json())     
        limit = data['total_count']   
        #limit = 50 
        for x in range(0, limit, 50):
            url = f'https://store.steampowered.com/search/results/?query&start={x}&count=50&dynamic_data=&force_infinite=1&category1=998&specials=1&snr=1_7_7_2300_7&infinite=1'
            #Hacemos un loop con todas las respuestas del servidor para obtener los links de los juegos
            yield scrapy.Request(url, callback=self.parse_links)

    def parse_links(self, response):
        data = json.loads(response.text)   
        selector = Selector(text=data['results_html'], type="html")
        for link in selector.css('a::attr(href)'):            
            url_game = ''.join(link.get())
            url_game = urllib.parse.unquote(url_game)
            print(url_game)
            #obtenemos los links de los juegos y llamamos otra funcion para obtener los datos que queremos
            yield scrapy.Request(url_game, cookies= {'birthtime': '283993201','mature_content': '1'}, callback=self.parse_info)

    def parse_info(self, response):
        yield{
            'name': urllib.parse.unquote(response.css('div.apphub_AppName::text').get()),
            'discount': response.css('div.discount_pct::text').get().replace('-', '').replace('%', ''),
            'orig_price': re.sub("[^\d.]", "", response.css('div.discount_original_price::text').get()),
            'disc_price': re.sub("[^\d.]", "", response.css('div.discount_final_price::text').get()),
            'tags': response.css('a.app_tag::text').getall(),
            'reviews': response.css('span.nonresponsive_hidden.responsive_reviewdesc::text').getall(),
            'link': response.url
        }

process = CrawlerProcess(settings={
    "FEEDS": {
        "steamgames.json": {"format": "json", "overwrite": True},
    },
})
process.crawl(steamcrawler)
process.start()