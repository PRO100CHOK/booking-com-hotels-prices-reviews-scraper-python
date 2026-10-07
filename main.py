"""Booking.com competitive-set rate audit for a hotel revenue manager.

Use case: you run a 4-star hotel in Amsterdam. Every week you want to know
which well-rated 4-5 star competitors are cheapest for a given stay, how deep
their discounts are, and how their nightly rate moves over the next two weeks.

Step 1 searches Booking.com for the competitive set (stars + review-score
filter, real dates). Step 2 builds a 14-day one-night price calendar for the
top hotels and reads the summary row the actor computes for each of them
(min / avg / max nightly price, cheapest date, sold-out days).

Run:
    pip install -r requirements.txt
    cp .env.example .env      # paste your APIFY_API_TOKEN
    python main.py

Actor: https://apify.com/pro100chok/booking-all-in-one-scraper?utm_source=github_pro100&utm_medium=readme&utm_campaign=booking-com-hotels-prices-reviews-scraper-python
"""
from __future__ import annotations

import csv
import json
import os
import sys
from datetime import date, timedelta
from pathlib import Path

from apify_client import ApifyClient
from apify_client.errors import ApifyApiError
from dotenv import load_dotenv

ACTOR_ID = "pro100chok/booking-all-in-one-scraper"
DESTINATION = "Amsterdam"
STARS = ["4", "5"]
MIN_SCORE = "8"          # Booking review-score bucket
MAX_HOTELS = 40          # competitive set size from search
CALENDAR_HOTELS = 5      # how many of them get a 14-day price calendar
CALENDAR_DAYS = 14
CURRENCY = "EUR"

OUT = Path(__file__).parent


def stay_dates(days_out: int = 21, nights: int = 2) -> tuple[str, str]:
    """A weekend-ish stay three weeks from today, so the script never goes stale."""
    check_in = date.today() + timedelta(days=days_out)
    return check_in.isoformat(), (check_in + timedelta(days=nights)).isoformat()


def run_actor(client: ApifyClient, run_input: dict, label: str) -> list[dict]:
    print(f"  running {label} ...")
    try:
        run = client.actor(ACTOR_ID).call(run_input=run_input, timeout_secs=1800)
    except ApifyApiError as exc:
        sys.exit(f"{label} failed: {exc}")
    return list(client.dataset(run["defaultDatasetId"]).iterate_items())


def main() -> int:
    load_dotenv()
    token = os.environ.get("APIFY_API_TOKEN")
    if not token:
        sys.exit("APIFY_API_TOKEN missing - copy .env.example to .env first.")
    client = ApifyClient(token)
    check_in, check_out = stay_dates()

    # Step 1 - the competitive set for one concrete stay
    print(f"Step 1/2 - {'/'.join(STARS)}-star hotels in {DESTINATION} rated {MIN_SCORE}+ "
          f"for {check_in} -> {check_out}")
    props = run_actor(client, {
        "scrapeType": "search",
        "searchQueries": [DESTINATION],
        "starRating": STARS,
        "minScore": MIN_SCORE,
        "checkIn": check_in,
        "checkOut": check_out,
        "adults": 2,
        "rooms": 1,
        "currency": CURRENCY,
        "language": "en-gb",
        "sortBy": "review_score_and_price",
        "maxItems": MAX_HOTELS,
    }, "search")
    props = [p for p in props if p.get("dataType") == "property" and not p.get("isSoldOut")]
    if not props:
        sys.exit("No available properties found - try other dates or filters.")

    props.sort(key=lambda p: p.get("pricePerNight") or p.get("price") or 1e9)
    print(f"  {len(props)} bookable hotels. Cheapest per night:")
    for p in props[:10]:
        disc = p.get("discountPercentage")
        print(f"    {CURRENCY} {p.get('pricePerNight') or p.get('price'):>8}  "
              f"{p.get('stars') or '-'}*  {p.get('rating') or '-':>4}  "
              f"{'-' + str(disc) + '%' if disc else '     '}  "
              f"{(p.get('district') or '')[:18]:<18}  {p.get('name')}")

    discounted = [p for p in props if p.get("discountPercentage")]
    print(f"  {len(discounted)}/{len(props)} competitors are running a discount right now")

    # Step 2 - 14-day nightly calendar for the best-rated hotels of the set
    top = sorted(props, key=lambda p: -(p.get("rating") or 0))[:CALENDAR_HOTELS]
    print(f"\nStep 2/2 - {CALENDAR_DAYS}-day price calendar for {len(top)} top-rated hotels")
    rows = run_actor(client, {
        "scrapeType": "prices",
        "startUrls": [{"url": p["url"]} for p in top if p.get("url")],
        "daysAhead": CALENDAR_DAYS,
        "checkIn": (date.today() + timedelta(days=7)).isoformat(),
        "adults": 2,
        "currency": CURRENCY,
        "language": "en-gb",
    }, "price calendar")
    calendars = [r for r in rows if r.get("dataType") == "priceCalendar"]
    for c in calendars:
        print(f"    {(c.get('hotelName') or '')[:36]:<36} "
              f"min {c.get('minPricePerNight')}  avg {c.get('avgPricePerNight')}  "
              f"max {c.get('maxPricePerNight')}  cheapest {c.get('cheapestDate')}  "
              f"sold-out days {c.get('soldOutDays')}/{c.get('totalDays')}")

    # Save everything for spreadsheets / BI tools
    (OUT / "output.json").write_text(json.dumps(
        {"competitiveSet": props, "priceCalendar": calendars, "roomOffers":
         [r for r in rows if r.get("dataType") == "price"]},
        indent=2, ensure_ascii=False), encoding="utf-8")
    fields = ["name", "stars", "rating", "reviewsCount", "pricePerNight", "price",
              "priceBeforeDiscount", "discountPercentage", "currency", "district",
              "freeCancellation", "mealPlan", "url"]
    with (OUT / "output.csv").open("w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=fields, extrasaction="ignore")
        w.writeheader()
        w.writerows(props)
    print("\nSaved output.json and output.csv")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
