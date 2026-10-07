"""Find under-priced, well-reviewed Booking.com stays and export them to CSV.

Searches three cities for the same dates, then uses pandas to keep hotels with a
score of 8.5+ that cost less than the city median per night, and flags active
discounts (price vs. priceBeforeDiscount).

Actor: https://apify.com/pro100chok/booking-all-in-one-scraper?utm_source=github_pro100&utm_medium=readme&utm_campaign=booking-com-hotels-prices-reviews-scraper-python
"""
import os
from datetime import date, timedelta

import pandas as pd
from apify_client import ApifyClient
from dotenv import load_dotenv

check_in = date.today() + timedelta(days=30)
check_out = check_in + timedelta(days=3)

load_dotenv()
client = ApifyClient(os.environ["APIFY_API_TOKEN"])

run = client.actor("pro100chok/booking-all-in-one-scraper").call(run_input={
    "scrapeType": "search",
    "searchQueries": ["Vienna", "Prague", "Budapest"],
    "checkIn": check_in.isoformat(),
    "checkOut": check_out.isoformat(),
    "adults": 2,
    "currency": "EUR",
    "maxItems": 100,
    "sortBy": "review_score_and_price",
})

df = pd.DataFrame(client.dataset(run["defaultDatasetId"]).iterate_items())
df = df[df["dataType"] == "property"]
df["pricePerNight"] = pd.to_numeric(df["pricePerNight"], errors="coerce")
df["rating"] = pd.to_numeric(df["rating"], errors="coerce")
df["cityMedian"] = df.groupby("searchQuery")["pricePerNight"].transform("median")

deals = df[(df["rating"] >= 8.5) & (df["pricePerNight"] < df["cityMedian"])]
deals = deals.sort_values(["searchQuery", "pricePerNight"])

cols = ["searchQuery", "name", "stars", "rating", "reviewsCount", "pricePerNight",
        "cityMedian", "priceBeforeDiscount", "discountPercentage", "district",
        "freeCancellation", "bookingUrl"]
deals[[c for c in cols if c in deals.columns]].to_csv("booking_deals.csv", index=False)
print(deals.groupby("searchQuery").size().rename("deals").to_string())
print(f"\nSaved {len(deals)} rows to booking_deals.csv")
