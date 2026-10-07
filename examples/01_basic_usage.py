"""List 25 Booking.com hotels in Lisbon with price, stars and review score.

Actor: https://apify.com/pro100chok/booking-all-in-one-scraper?utm_source=github_pro100&utm_medium=readme&utm_campaign=booking-com-hotels-prices-reviews-scraper-python
"""
import os

from apify_client import ApifyClient
from dotenv import load_dotenv

load_dotenv()
client = ApifyClient(os.environ["APIFY_API_TOKEN"])

run = client.actor("pro100chok/booking-all-in-one-scraper").call(run_input={
    "scrapeType": "search",
    "searchQueries": ["Lisbon"],
    "maxItems": 25,
    "currency": "EUR",
})

for h in client.dataset(run["defaultDatasetId"]).iterate_items():
    print(f"{h.get('rating') or '-':>4}  {h.get('stars') or '-'}*  "
          f"{h.get('priceRounded') or '-':>8}  {h.get('name')}  ({h.get('distanceFromCenter') or ''})")
