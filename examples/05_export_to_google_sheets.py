"""Daily Booking.com rate shopping log in a Google Sheet.

Setup:
  1. Google Cloud console -> create a service account -> download its JSON key.
  2. Save it as service_account.json next to this file (it is gitignored).
  3. Share the spreadsheet with the service account's email address.
  4. Put your competitors' Booking.com hotel URLs in COMPETITORS.

Each run appends one row per competitor with the 30-day calendar summary the actor
computes in Prices mode (min / avg / max nightly rate, cheapest date, sold-out days,
occupancy). Schedule it daily on Apify or with cron to build a price history.

Actor: https://apify.com/pro100chok/booking-all-in-one-scraper?utm_source=github_pro100&utm_medium=readme&utm_campaign=booking-com-hotels-prices-reviews-scraper-python
"""
import os
from datetime import datetime, timezone

import gspread
from apify_client import ApifyClient
from dotenv import load_dotenv
from google.oauth2.service_account import Credentials

SPREADSHEET = "Booking.com rate shopping"
WORKSHEET = "calendar"
COMPETITORS = [
    "https://www.booking.com/hotel/nl/pulitzer-amsterdam.html",
]
SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]

load_dotenv()
client = ApifyClient(os.environ["APIFY_API_TOKEN"])

run = client.actor("pro100chok/booking-all-in-one-scraper").call(run_input={
    "scrapeType": "prices",
    "startUrls": [{"url": u} for u in COMPETITORS],
    "daysAhead": 30,
    "adults": 2,
    "currency": "EUR",
})

header = ["collected_at", "hotel", "currency", "min_per_night", "avg_per_night",
          "max_per_night", "cheapest_date", "most_expensive_date", "available_days",
          "sold_out_days", "occupancy_rate", "url"]
stamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M")
rows = [[stamp, r.get("hotelName"), r.get("currency"), r.get("minPricePerNight"),
         r.get("avgPricePerNight"), r.get("maxPricePerNight"), r.get("cheapestDate"),
         r.get("mostExpensiveDate"), r.get("availableDays"), r.get("soldOutDays"),
         r.get("occupancyRate"), r.get("url")]
        for r in client.dataset(run["defaultDatasetId"]).iterate_items()
        if r.get("dataType") == "priceCalendar"]

creds = Credentials.from_service_account_file("service_account.json", scopes=SCOPES)
sheet = gspread.authorize(creds).open(SPREADSHEET)
try:
    ws = sheet.worksheet(WORKSHEET)
except gspread.WorksheetNotFound:
    ws = sheet.add_worksheet(WORKSHEET, rows=5000, cols=len(header))
    ws.append_row(header)

ws.append_rows(rows, value_input_option="USER_ENTERED")
print(f"Appended {len(rows)} calendar rows to {SPREADSHEET}/{WORKSHEET}")
