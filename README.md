# Booking.com Hotels, Prices & Reviews Scraper — Python Example

> Pull Booking.com hotel listings, room prices, a price calendar up to a year ahead, guest reviews with category scores, full property details and professional host contacts into Python — no partner agreement, no browser, no login.

[![Apify Actor](https://img.shields.io/badge/Apify-Actor-blue)](https://apify.com/pro100chok/booking-all-in-one-scraper?utm_source=github_pro100&utm_medium=readme&utm_campaign=booking-com-hotels-prices-reviews-scraper-python)
[![Python 3.10+](https://img.shields.io/badge/Python-3.10+-green)](https://python.org)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow)](LICENSE)

A small, working Python project built on the [Booking.com Scraper API actor on Apify](https://apify.com/pro100chok/booking-all-in-one-scraper?utm_source=github_pro100&utm_medium=readme&utm_campaign=booking-com-hotels-prices-reviews-scraper-python). The scripts here show how revenue managers, travel startups and analysts turn Booking.com into a dataset they can query: rate shopping against a competitive set, review mining, hotel catalogue enrichment and B2B lead lists of property managers.

## What this does

Booking.com's official API is reserved for contracted partners, and it is built for selling rooms, not for reading the market. This actor is a practical **unofficial Booking.com API**: you send JSON input, it returns structured records for whatever you asked for.

Under the hood it talks to Booking.com pages and Booking's internal GraphQL API over plain HTTP — no headless browser. Booking protects non-browser traffic with an AWS WAF challenge; the actor solves it automatically and re-solves it when it expires. Search results and reviews are paginated through GraphQL, so page 2 really is page 2 (the `offset=` URL trick many scrapers rely on silently returns page 1 again).

Every record carries a `dataType` field — `property`, `price`, `priceCalendar`, `review`, `reviewScores`, `hotel` or `host` — so a mixed export can be split with one filter.

## Six scrape modes

| `scrapeType` | What you get | Starts from |
|---|---|---|
| `search` | One `property` row per hotel: price, price per night, pre-discount price, discount badges, stars, review score, location sub-score, meal plan, free cancellation, district, GPS, sold-out flag | `searchQueries` or Booking search URLs |
| `prices` | One `price` row per room offer (room, occupancy, meal plan, price, original price, free-cancellation deadline, `roomsLeft`) and, with `daysAhead`, a `priceCalendar` summary per hotel | Destinations, search URLs or hotel URLs |
| `reviews` | Every guest review (score, title, positive and negative text, country, room type, stay dates, owner reply) plus one `reviewScores` row per hotel | Hotel URLs or a destination |
| `hotelDetails` | Full profile: description, facilities and amenity names, policies, payment methods, room-by-room configuration, licence numbers, Q&A, Booking's review summary (pros/cons with mention counts), surroundings | Hotel URLs |
| `hostInfo` | Professional host block (company, registration number, email, phone, address) plus host profile and number of managed properties | Hotel URLs or a destination |
| `all` | Details + host + reviews nested in one record per hotel | Hotel URLs |

In `search` mode you can also set `enrichWith` to `hotelDetails`, `prices`, `reviews` and/or `host`. The actor then drills into every hotel it finds and nests the extra data inside the same row — one tidy record per property instead of four scattered datasets.

## Use cases

- **Rate shopping for hotels** — track competitors' nightly rates, discount depth and "rooms left" scarcity for your exact dates.
- **Price calendars** — one-night prices for up to 365 consecutive days, summarised into min/avg/max, cheapest date and sold-out days.
- **Review and sentiment analysis** — full positive/negative review text and category scores (staff, cleanliness, comfort, value, location, Wi-Fi) for NLP models.
- **Hotel catalogue enrichment** — facilities, room sizes, bed types, check-in windows, policies and what's nearby for travel apps.
- **Property-manager lead generation** — company, email and phone that professional hosts are legally required to publish in the EU.
- **Market research** — inventory, star mix and price distribution of a city, split by district.
- **Short-term rental compliance** — the licence numbers hosts must display in regulated markets.

## Requirements

- Python **3.10+**
- A free [Apify account](https://console.apify.com/sign-up) — the free plan includes $5 of usage every month
- No Booking.com account, cookies or tokens

## Quick start

```bash
git clone https://github.com/pro100chok/booking-com-hotels-prices-reviews-scraper-python.git
cd booking-com-hotels-prices-reviews-scraper-python
pip install -r requirements.txt
cp .env.example .env
# paste your APIFY_API_TOKEN into .env
python main.py
```

The token comes from Apify Console → Settings → Integrations. The actor itself lives at [apify.com/pro100chok/booking-all-in-one-scraper](https://apify.com/pro100chok/booking-all-in-one-scraper?utm_source=github_pro100&utm_medium=readme&utm_campaign=booking-com-hotels-prices-reviews-scraper-python).

## How `main.py` works

`main.py` is a weekly competitive-set audit for a 4-star hotel in Amsterdam:

1. **Search** — `scrapeType: "search"` with `starRating: ["4", "5"]`, `minScore: "8"`, real check-in/check-out dates three weeks from today and `sortBy: "review_score_and_price"`. Sold-out properties are dropped, the rest are ranked by price per night and the share of competitors running a discount is printed.
2. **Price calendar** — the five best-rated hotels go back into the actor with `scrapeType: "prices"` and `daysAhead: 14`. The actor returns room offers for each night plus one `priceCalendar` row per hotel with `minPricePerNight`, `avgPricePerNight`, `maxPricePerNight`, `cheapestDate` and `soldOutDays`.
3. **Save** — everything goes to `output.json`, the competitive set to `output.csv`.

Dates are computed from today, so the script never quotes an expired stay.

## Example output

A `property` record from search mode (shortened):

```json
{
  "dataType": "property",
  "name": "Mercure Amsterdam Sloterdijk Station",
  "stars": 4,
  "rating": 8.6,
  "ratingLabel": "Excellent",
  "reviewsCount": 4177,
  "price": 126.21,
  "priceRounded": "$126",
  "currency": "USD",
  "city": "Amsterdam",
  "countryCode": "nl",
  "latitude": 52.387911,
  "longitude": 4.834296,
  "distanceFromCenter": "4.3 km from downtown",
  "hostType": "PROFESSIONAL",
  "isSoldOut": false
}
```

A `priceCalendar` row adds `totalDays`, `availableDays`, `soldOutDays`, `occupancyRate`, `minPricePerNight`, `avgPricePerNight`, `maxPricePerNight`, `cheapestDate`, `mostExpensiveDate` and `bookingUrl`. Empty fields are omitted rather than returned as `null` — Booking simply does not publish every field for every property.

## Input parameters

| Parameter | Type | Description |
|---|---|---|
| `scrapeType` | enum | `search`, `prices`, `reviews`, `hotelDetails`, `hostInfo`, `all` (required) |
| `searchQueries` | array | Destinations such as `Amsterdam`, `Paris, France`, `Bali` |
| `startUrls` | array | Booking.com hotel or search URLs, pasted from the browser |
| `maxItems` | integer | Max properties per destination (default 50) |
| `enrichWith` | array | Search mode only: `hotelDetails`, `prices`, `reviews`, `host` |
| `maxReviews` | integer | Max reviews per hotel (default 100) |
| `sortReviewsBy` | enum | `relevance`, `newest`, `oldest`, `score_high`, `score_low` |
| `includeSurroundings` | boolean | Nearby landmarks, transport, airports, beaches with hotel details (default on) |
| `checkIn` / `checkOut` | string | `YYYY-MM-DD` |
| `daysAhead` | integer | Prices mode: 0–365 one-night stays from the check-in date |
| `adults`, `children`, `childrenAges`, `rooms` | — | Occupancy |
| `currency` / `language` | string | e.g. `EUR`, `en-gb` |
| `sortBy` | enum | `relevance`, `popularity`, `price`, `review_score`, `review_score_and_price`, `stars_high`, `stars_low`, `distance` |
| `starRating`, `minScore`, `minPrice`, `maxPrice` | — | Search filters |
| `maxConcurrency`, `maxRetries`, `proxyConfiguration` | — | Advanced; the default Apify Proxy setting works out of the box |

## More examples

| File | What it shows |
|---|---|
| [`examples/01_basic_usage.py`](examples/01_basic_usage.py) | 25 Lisbon hotels with price, stars and score |
| [`examples/02_guest_reviews.py`](examples/02_guest_reviews.py) | Newest reviews for one hotel, category scores, guest countries, worst stays |
| [`examples/03_host_contacts_leads.py`](examples/03_host_contacts_leads.py) | Property-manager emails and phones for Barcelona saved to CSV |
| [`examples/04_export_to_csv.py`](examples/04_export_to_csv.py) | pandas: 8.5+ hotels priced below the city median in three cities |
| [`examples/05_export_to_google_sheets.py`](examples/05_export_to_google_sheets.py) | Daily 30-day price calendar appended to a Google Sheet |

## Ready-made tasks

Prefer a preconfigured run? These public tasks open the actor with the input already filled in:

- [Search Booking.com hotels in any destination](https://apify.com/pro100chok/booking-search-hotels-in-destination?utm_source=github_pro100&utm_medium=readme&utm_campaign=booking-com-hotels-prices-reviews-scraper-python)
- [Track Booking.com room prices day by day](https://apify.com/pro100chok/booking-price-calendar-monitoring?utm_source=github_pro100&utm_medium=readme&utm_campaign=booking-com-hotels-prices-reviews-scraper-python)
- [Export guest reviews for any Booking.com hotel](https://apify.com/pro100chok/booking-hotel-guest-reviews?utm_source=github_pro100&utm_medium=readme&utm_campaign=booking-com-hotels-prices-reviews-scraper-python)
- [Find Booking.com host and owner information](https://apify.com/pro100chok/booking-host-and-owner-contacts?utm_source=github_pro100&utm_medium=readme&utm_campaign=booking-com-hotels-prices-reviews-scraper-python)
- [Search only high-rated hotels in a price range](https://apify.com/pro100chok/booking-filtered-luxury-hotel-search?utm_source=github_pro100&utm_medium=readme&utm_campaign=booking-com-hotels-prices-reviews-scraper-python)

## How much does it cost to scrape Booking.com?

Pay per result; proxies and compute are included. Prices per 1,000 results on the free plan, with the Gold-plan rate in brackets:

| Result | Free plan | Gold |
|---|---|---|
| Property (search result) | $1.50 | $0.70 |
| Room price offer | $3.00 | $1.20 |
| Guest review | $2.00 | $0.40 |
| Review category scores (per hotel) | $3.00 | $1.00 |
| Hotel details | $4.00 | $2.00 |
| Host / owner contact | $5.00 | $2.50 |

There is also a tiny actor-start fee of $0.00005 per run. The free monthly $5 covers roughly 3,300 search results. Keep `maxItems`, `maxReviews` and `daysAhead` small while testing.

## FAQ

**Do I need a Booking.com account or API key?** No. The actor reads public pages; your only credential is the Apify token in `.env`.

**Can I get every hotel in a city?** Booking.com returns at most about 1,000 properties per query. For bigger markets, split the search by `starRating` or `minPrice` / `maxPrice` and merge the results.

**How do I monitor prices over time?** Use `prices` mode with `daysAhead`, then schedule the run on Apify or run `examples/05_export_to_google_sheets.py` from cron. Each run appends a new calendar snapshot.

**Why do some hotels have no host contact?** Only professional hosts publish the trader contact block. Private hosts don't, and the actor returns nothing rather than guessing.

**Can I get reviews in a particular order?** Yes — `sortReviewsBy` accepts newest, oldest, highest or lowest score. Every review record also includes its `language`.

**Does it support other currencies and languages?** Any Booking.com supports: set `currency` (USD, EUR, GBP…) and `language` (en-us, en-gb, de, fr, es, it…).

**Can AI agents use it?** Yes, through the Apify MCP server — Claude, Cursor and other MCP clients can call the actor as a tool.

## Related actors

- [TripAdvisor Scraper API](https://apify.com/pro100chok/tripadvisor-all-in-one?utm_source=github_pro100&utm_medium=readme&utm_campaign=booking-com-hotels-prices-reviews-scraper-python) — cross-check hotel ratings and reviews on TripAdvisor.
- [Expedia Scraper API](https://apify.com/pro100chok/expedia-all-in-one-scraper?utm_source=github_pro100&utm_medium=readme&utm_campaign=booking-com-hotels-prices-reviews-scraper-python) — the same hotels' Expedia prices, rate plans and reviews for parity checks.
- [Google Maps Scraper API](https://apify.com/pro100chok/google-maps-scraper?utm_source=github_pro100&utm_medium=readme&utm_campaign=booking-com-hotels-prices-reviews-scraper-python) — Google reviews, photos and phone numbers for each property.
- [Website Contact Scraper](https://apify.com/pro100chok/extract-emails?utm_source=github_pro100&utm_medium=readme&utm_campaign=booking-com-hotels-prices-reviews-scraper-python) — turn hotel websites into emails, phones and social profiles.

## License

MIT — see [LICENSE](LICENSE). This repository contains example client code only; the scraper runs on Apify.

---

Built by [pro100chok](https://apify.com/pro100chok/booking-all-in-one-scraper?utm_source=github_pro100&utm_medium=readme&utm_campaign=booking-com-hotels-prices-reviews-scraper-python) · Scrape Booking.com responsibly and in line with GDPR and Booking.com's terms.
