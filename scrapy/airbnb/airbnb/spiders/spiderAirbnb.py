import scrapy
from unicode_tr import unicode_tr
import logzero
import logging
from logzero import logger as lg
logzero.loglevel(logging.DEBUG) # To display content information


def prepare_request(city, checkin=None, checkout=None, price_min=None, price_max=None, currency='USD',flexi = True, area_id = None):
    """ Given a city and eventual dates, and eventual prices, returns the airbnb url to scrap
        Both dates must be strings formatted 'YYYY-MM-DD'
    """
    url = f'https://www.airbnb.com/s/{city}/homes/?' 
    
    if flexi == True:
        url += f'&flexible_trip_dates%5B%5D=april&flexible_trip_lengths%5B%5D=weekend_trip&flexible_trip_dates%5B%5D=march' 
    if checkin and checkout and flexi == False:
        url += f'&checkin={checkin}&checkout={checkout}'
    if price_min and price_max:
        url+= f'&price_min={price_min}&price_max={price_max}&display_currency={currency}'
    if area_id :
        url += f'&neighborhood_ids%5B%5D={area_id}'    
        
        
    return url

class AirbnbSpider(scrapy.Spider):
    name = "AirbnbSpider"

    def __init__(self, *args, **kwargs):
    
        # Web pages to parse
        
        import pandas as pd
        import numpy as np
        areas = {'area_id':  [2411,2341,2488,2350,2340,2339,2445,2526,2342,2525,2524,2431,2523,2444,2443],
               'area_name' : ['aksaray','beyoglu','besiktas','cihangir','eminonu','fatih','kadikoy','kadikoy merkez','karakoy','moda','ortakoy','sultanahmet','taksim','uskudar','sisli']   }
        areas_df = pd.DataFrame(areas)
        pricelevels = {'levels' : [1,2,3,4,5,6,7,8,9,10,11],
                       'Min'    : [1,20,26,31,37,43,48,55,66,77,101],
                       'Max'    : [20,25,31,36,42,47,54,65,76,100,500] }

        price_levels_df = pd.DataFrame(pricelevels)

        url_list = []

        for area in range(0, areas_df.shape[0]-1):
            for minmax in range (0, price_levels_df.shape[0]-1):
                url_list.append(prepare_request('istanbul--Turkey', '2021-04-09', '2021-04-12', price_min=price_levels_df['Min'][minmax], price_max=price_levels_df['Max'][minmax],area_id = areas_df['area_id'][area],flexi =False))
        self.start_urls = url_list
        #self.start_urls = [prepare_request('istanbul--Turkey', '2021-04-09', '2021-04-12', price_min=90, price_max=110,area_id = 2445,flexi =False),prepare_request('istanbul--Turkey', '2021-04-09', '2021-04-12', price_min=90, price_max=110,area_id = 2488,flexi =False)]
        # Parse max_page
        self.max_page = 15
        # Scrapping compteur
        self.page = 0
        self.object = 0


    def start_requests(self):
        for url in self.start_urls:
            yield scrapy.Request(url=url, callback=self.parse)


    def parse(self, response):

        # Number of main page scrapped
        self.page += 1
        lg.warn('Parse page ({})'.format(self.page))

        # Loading all add on the webpage
        annonces = response.css('div._8ssblpx')

        # Iteratint on each of them to yield adds in a JSON file
        for annonce in annonces:

            titre = annonce.css('a ::attr(aria-label)').extract_first()
            lien = annonce.css('::attr(href)').extract_first()
            img_url = annonce.css('img ::attr(src)').extract_first()
            type_of_room = annonce.css('div._b14dlit ::text').extract_first()

            additionnal_info = annonce.css('div._kqh46o ::text').extract()
            additionnal_info = [i for i in additionnal_info if i not in [' · ']]

            rating = annonce.css('span._10fy1f8 ::text').extract_first()
            nb_comment = annonce.css('span._a7a5sx ::text').extract()
            
            night_price = annonce.css('span._olc9rf0 ::text').extract()
            full_price = annonce.css('span._7nl8mr ::text').extract()

            superhost = annonce.css('div._ufoy4t::text').extract()
            superhost = 'SUPERHOST' in superhost       


            lg.debug(titre)
            yield {
                'titre':titre,
                'lien':lien,
                'img_url':img_url,
                'type_of_room':type_of_room,
                'additionnal_info':additionnal_info,
                'rating':rating,
                'nb_comment':nb_comment,
                'night_price':night_price,
                'full_price':full_price,
                'superhost':superhost
                }
     
        next_page = response.css('a._za9j7e ::attr(href)').extract()
        lg.warn(len(next_page))
        
        if next_page is not None:
            if len(next_page)>0:
                next_page = next_page[0]
                url = "https://www.airbnb.com" + next_page + '&display_currency=USD'
                yield scrapy.Request(url=url, callback=self.parse)
        else:
            lg.error('No next page')