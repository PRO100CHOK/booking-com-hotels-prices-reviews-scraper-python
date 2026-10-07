"""Newest Booking.com guest reviews for one hotel + its category scores.

Reviews mode returns two kinds of records (filter by `dataType`):
  - "review"        one per guest review (score, positive/negative text, country...)
  - "reviewScores"  one per hotel (staff, cleanliness, comfort, value, location...)

Actor: https://apify.com/pro100chok/booking-all-in-one-scraper?utm_source=github_pro100&utm_medium=readme&utm_campaign=booking-com-hotels-prices-reviews-scraper-python
"""
import os
from collections import Counter

from apify_client import ApifyClient
from dotenv import load_dotenv

HOTEL_URL = "https://www.booking.com/hotel/nl/pulitzer-amsterdam.html"

load_dotenv()
client = ApifyClient(os.environ["APIFY_API_TOKEN"])

run = client.actor("pro100chok/booking-all-in-one-scraper").call(run_input={
    "scrapeType": "reviews",
    "startUrls": [{"url": HOTEL_URL}],
    "maxReviews": 150,
    "sortReviewsBy": "newest",
})

items = list(client.dataset(run["defaultDatasetId"]).iterate_items())
reviews = [r for r in items if r.get("dataType") == "review"]
scores = [r for r in items if r.get("dataType") == "reviewScores"]

for block in scores:
    print(f"Category scores ({block.get('totalReviews')} reviews):")
    for s in block.get("scores") or []:
        print(f"  {s.get('label') or s.get('name'):<22} {s.get('value')}")

print(f"\n{len(reviews)} reviews. Guests by country:")
for country, n in Counter(r.get("userCountry") or "-" for r in reviews).most_common(8):
    print(f"  {n:>3}  {country}")

print("\nLowest-scored recent stays:")
for r in sorted(reviews, key=lambda r: r.get("score") or 10)[:5]:
    print(f"  [{r.get('score')}] {r.get('reviewDate')}  {r.get('roomType') or ''}")
    print(f"     - {(r.get('negativeText') or '')[:160]}")
