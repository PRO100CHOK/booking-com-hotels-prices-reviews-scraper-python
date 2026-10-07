"""Property-manager lead list from Booking.com host contacts.

Host mode reads the business contact block that professional hosts publish on
Booking.com (company, registration number, email, phone, address) plus the host
profile. With a destination instead of URLs, the top hotels of that search are used.
Private hosts have no such block, so expect fewer rows than hotels.

Actor: https://apify.com/pro100chok/booking-all-in-one-scraper?utm_source=github_pro100&utm_medium=readme&utm_campaign=booking-com-hotels-prices-reviews-scraper-python
"""
import csv
import os

from apify_client import ApifyClient
from dotenv import load_dotenv

load_dotenv()
client = ApifyClient(os.environ["APIFY_API_TOKEN"])

run = client.actor("pro100chok/booking-all-in-one-scraper").call(run_input={
    "scrapeType": "hostInfo",
    "searchQueries": ["Barcelona"],
    "maxItems": 60,
})

leads = [h for h in client.dataset(run["defaultDatasetId"]).iterate_items()
         if h.get("email") or h.get("phone")]

fields = ["hotelName", "companyName", "personName", "hostName", "email", "phone",
          "registrationNumber", "managedProperties", "city", "countryCode"]
with open("host_leads.csv", "w", newline="", encoding="utf-8") as fh:
    w = csv.DictWriter(fh, fieldnames=fields, extrasaction="ignore")
    w.writeheader()
    w.writerows(leads)

for h in leads[:15]:
    print(f"{(h.get('companyName') or h.get('hostName') or '-')[:32]:<32} "
          f"{h.get('email') or '-':<34} {h.get('phone') or '-'}")
print(f"\n{len(leads)} contactable hosts saved to host_leads.csv")
