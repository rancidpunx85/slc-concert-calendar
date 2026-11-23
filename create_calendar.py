
import json
from datetime import datetime
from zoneinfo import ZoneInfo
from icalendar import Calendar, Event

with open("slc_concerts.json") as file:
    concerts = json.load(file)

calendar = Calendar()
calendar.add("prodid", "-//SLC Concert Calendar//EN")
calendar.add("version", "2.0")
calendar.add("x-wr-calname", "My Spotify Concerts")

timezone = ZoneInfo("America/Denver")

for concert in concerts:
    if not concert.get("date"):
        continue

    event = Event()

    start = datetime.fromisoformat(
        concert["date"]
    ).replace(tzinfo=timezone)

    event.add("summary", concert["artist"] + " - Live")
    event.add("dtstart", start)
    event.add("dtend", start.replace(
        hour=min(start.hour + 2, 23)
    ))

    event.add(
        "location",
        f"{concert.get('venue') or 'Venue TBA'}, "
        f"{concert.get('city') or 'Utah'}"
    )

    if concert.get("url"):
        event.add("url", concert["url"])
        event.add("description", concert["url"])

    event.add(
        "uid",
        f"{concert['artist']}-{concert['date']}@slcconcerts"
    )

    calendar.add_component(event)

with open("slc_concerts.ics", "wb") as file:
    file.write(calendar.to_ical())

print(f"Created calendar with {len(concerts)} concerts!")

