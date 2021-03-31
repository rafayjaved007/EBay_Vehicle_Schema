import json

import requests
import scrapy
from ..items import EbayVehiclesItem


class EBayVehicleSpider(scrapy.Spider):
    name = 'car_spider'
    start_urls = ['https://www.ebay.com/b/Auto-Parts-and-Vehicles/6000/bn_1865334']

    custom_settings = {
        'HTTPPROXY_ENABLED': True
    }
    headers = {
        'Referer': 'https://www.ebay.com/b/Auto-Parts-and-Vehicles/6000/bn_1865334',
        'Origin': 'https://www.ebay.com',
        'x-ebay-c-tracking': 'guid=787de1fd1780a7b1d4e2d68affe15716,pageid=2499334,cobrandId=0',
        'x-ebay-c-cultural-pref': 'x-ebay-c-cultural-pref',
        'authorization': 'Bearer v^1.1#i^1#I^3#p^1#r^1#f^0#t^Ul43Xzg6ODRCNzY3NjY1MzJGMzRDQUVDQ0JERTE5QjMyNjg0NzJfMV8xI0VeMjYw',
        'rlogid': 't6o%60~eqr%60b77%3C%3Dosukf%7Ddutcc31(aqk%7Fq*w%60ut355%3F-178787de1ec-0x1402',
        'x-ebay-c-enduserctx': 'ip=77.111.246.39,userAgentAccept=text%2Fhtml%2Capplication%2Fxhtml%2Bxml%2Capplication%2Fxml%3Bq%3D0.9%2Cimage%2Favif%2Cimage%2Fwebp%2Cimage%2Fapng%2C*%2F*%3Bq%3D0.8%2Capplication%2Fsigned-exchange%3Bv%3Db3%3Bq%3D0.9,userAgentAcceptEncoding=gzip,userAgent=Mozilla%2F5.0%20(Windows%20NT%2010.0%3B%20Win64%3B%20x64)%20AppleWebKit%2F537.36%20(KHTML%2C%20like%20Gecko)%20Chrome%2F88.0.4324.192%20Safari%2F537.36%20OPR%2F74.0.3911.218,uri=%2Fb%2FAuto-Parts-and-Vehicles%2F6000%2Fbn_1865334,applicationURL=https%3A%2F%2Fwww.ebay.com%2Fb%2FAuto-Parts-and-Vehicles%2F6000%2Fbn_1865334,xff=77.111.246.39%2C23.200.158.27%2C209.140.129.29%2C10.68.213.151,expectSecureURL=true,physicalLocation=country%3DUS%2Czip%3D60629',
        'Accept': 'application/json',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/88.0.4324.192 Safari/537.36 OPR/74.0.3911.218',
        'accept-language': 'en-US',
        'X-Requested-With': 'XMLHttpRequest',
        'x-ebay-c-marketplace-id': 'EBAY-US'
    }

    def start_requests(self):
        for year in range(1896, 1901):
            url = f'https://api.ebay.com/parts_compatibility/v1/get_automatic_metadata_selection?vehicle_marketplaceId=EBAY-US&vehicle_type=CAR_AND_TRUCK&Year={year}'
            request = scrapy.Request(url=url, callback=self.parse_item, meta={'year': year, 'url': url}, headers=self.headers)
            yield request

    def convert(self, url, req):
        
        def get_list(ind, name):
            try:
                res = requests.get(url=url, headers=self.headers)
                if 'nextPropertyChoice' in json.loads(res.text).keys():
                    if json.loads(res.text)['nextPropertyChoice']['name'] == name:
                        return json.loads(res.text)['nextPropertyChoice']['possibleValues']
                    else:
                        return json.loads(res.text)['selectedProperties'][ind]['possibleValues']
                else:
                    return json.loads(res.text)['selectedProperties'][ind]['possibleValues']
            except KeyError:
                return []

        if req == 'model':
            model_list = get_list(2, 'Model')
            if len(model_list) != 0:
                return model_list
            else:
                return get_list(2, 'Model')
            
        elif req == 'trim':
            trim_list = get_list(3, 'Trim')
            if len(trim_list) != 0:
                return trim_list
            else:
                return get_list(3, 'Trim')
            
        elif req == 'engine':
            engine_list = get_list(4, 'Engine')
            if len(engine_list) != 0:
                return engine_list
            else:
                return get_list(4, 'Engine')

    def parse_item(self, response):
        item = EbayVehiclesItem()

        url = response.meta.get('url')
        year = response.meta.get('year')
        if 'nextPropertyChoice' in json.loads(response.text).keys():
            make_list = json.loads(response.text)['nextPropertyChoice']['possibleValues']
        else:
            make_list = json.loads(response.text)['selectedProperties'][1]['possibleValues']

        for make in make_list:
            make_model = {}
            model_trim = {}

            model_list = self.convert(url=url+f'&Make={make.replace(" ","%20").replace("&","%26")}', req='model')
            for model in model_list:
                trim_list = self.convert(url=url+f'&Make={make.replace(" ","%20").replace("&","%26")}&Model={model.replace(" ","%20").replace("&","%26")}', req='trim')
                trim_engine = {}
                for trim in trim_list:
                    engine_list = self.convert(url=url+f'&Make={make.replace(" ","%20").replace("&","%26")}&Model={model.replace(" ","%20").replace("&","%26")}&Trim={trim.replace(" ","%20").replace("&","%26").replace("+","%2B")}', req='engine')
                    trim_engine.update({f'Trim: {trim}': f'Engines: {engine_list}'})
                model_trim.update({f'Model: {model}': trim_engine})
            make_model.update({f'Make: {make}': model_trim})

            item['Year'] = {year: make_model}
            yield item
