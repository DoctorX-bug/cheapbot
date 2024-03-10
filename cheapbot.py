import sys

import aiohttp
import discord
import skinport
from discord.ext import commands
from datetime import datetime

import config

if config.discord_webhook_url == '':
    print("You have to set a Discord Webhook URL in the config.py file", file=sys.stderr)
    sys.exit(1)

skinport_client = skinport.Client()

async def get_item_from_sales_history(market_hash_name: str) -> skinport.ItemWithSales:
    sales_history = await skinport_client.get_sales_history()
    return [item for item in sales_history if item.market_hash_name == market_hash_name][0]

@skinport_client.listen("saleFeed")
async def on_sale_feed(data):
    paginator = commands.Paginator(prefix="", suffix="")
    salefeed = skinport.SaleFeed(data=data)
    now = datetime.now()
    current_time = now.strftime("%H:%M")
    # curr_time = time.localtime() 
    # curr_clock = time.strftime("%H%М", curr_time)
    if current_time == "12:00":
        paginator.add_line(f"***Здравей милионерче: https://www.youtube.com/watch?v=0YqYe_CbfAs***")

    # Ignore "sold" events    
    if salefeed.event_type == "sold":
        return
    
    sales = salefeed.sales
    for s in sales:
        # discount = round(abs(s.suggested_price - s.sale_price) / ((s.suggested_price + s.sale_price)/2)*100, 2)
        discount = round((s.suggested_price-s.sale_price) / s.suggested_price*100,2)
        if discount > 30 and s.sale_price < 40:
            paginator.add_line(f"-_-_-_-_-_-\nDiscount {discount} \n {s.market_hash_name}: {s.sale_price} {s.currency} \n Float: {s.wear}\n<{s.url}>\n-_-_-_-_-_-")
            
        if discount < 20 or s.suggested_price < 2: # Ignore items which are suggested for less than 2 EUR
            return
        print("Name" ,s , "Sale Price", s.sale_price, "Suggested Price", s.suggested_price, "discount", discount, "Emergency link", s.url)
        
        if "case" in s.market_hash_name or "Case" in s.market_hash_name:
            return

        if "\u2605" in s.tags and s.stattrak: # Ignore StatTrak Knives
            return
        
        item = await get_item_from_sales_history(s.market_hash_name)
        if not item:
            return

        if (item.last_7_days.avg is not None and item.last_7_days.avg > s.sale_price) and s.sale_price < 25:
            paginator.add_line(f"-_-_-_-_-_-\nDiscount {discount} \n {s.market_hash_name}: {s.sale_price} {s.currency} \n Float: {s.wear}\n<{s.url}>\n-_-_-_-_-_-")

    async with aiohttp.ClientSession() as session:
        webhook = discord.Webhook.from_url(config.discord_webhook_url, session=session)
        for page in paginator.pages:
            await webhook.send(page)


if __name__ == "__main__":
    print(f"Running... on skinport.py {skinport.__version__}")
    skinport_client.run()