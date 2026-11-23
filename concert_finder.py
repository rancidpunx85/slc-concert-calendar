
import json
import time
import urllib.request
import urllib.parse
import urllib.error

import spotipy
from spotipy.oauth2 import SpotifyPKCE

# Cities in our four-county search area.
# This is a starter list, not a complete county boundary map.
CITIES = {
    "provo", "orem", "vineyard", "lindon",
    "pleasant grove", "american fork", "highland",
    "alpine", "cedar hills", "lehi", "saratoga springs",
    "eagle mountain", "spanish fork", "springville",
    "payson", "salem", "mapleton", "santaquin",
    "salt lake city", "south salt lake",
    "west valley city", "west jordan",
    "south jordan", "sandy", "draper",
    "midvale", "murray", "millcreek",
    "cottonwood heights", "holladay",
    "taylorsville", "riverton", "herriman",
    "bluffdale", "magna", "kearns",
    "bountiful", "north salt lake", "woods cross",
    "centerville", "farmington", "kaysville",
    "layton", "clearfield", "syracuse",
    "clinton", "west point", "fruit heights",
    "south weber", "sunset",
    "ogden", "south ogden", "north ogden",
    "west haven", "roy", "riverdale",
    "washington terrace", "harrisville",
    "farr west", "plain city", "pleasant view",
    "hooper", "huntsville", "eden", "liberty"
}

import os
client_id = os.environ["SPOTIFY_CLIENT_ID"]

auth = SpotifyPKCE(
    client_id=client_id,
    redirect_uri="http://127.0.0.1:8888/callback",
    scope="user-follow-read",
    cache_path=".spotify_cache",
    open_browser=False
)


# Use the saved refresh token when running in GitHub Actions.
refresh_token = os.environ.get("SPOTIFY_REFRESH_TOKEN")

if refresh_token:
    token_info = auth.refresh_access_token(refresh_token)
    spotify = spotipy.Spotify(
        auth=token_info["access_token"]
    )
else:
    # Keep the existing local Mac authorization.
    spotify = spotipy.Spotify(auth_manager=auth)


print("\nGetting your Spotify artists...")

artists = []
after = None

while True:
    result = spotify.current_user_followed_artists(
        limit=50, after=after
    )
    batch = result["artists"]["items"]
    if not batch:
        break

    artists.extend(batch)
    after = result["artists"]["cursors"]["after"]
    if not after:
        break

print("Total followed artists:", len(artists))

# Test 15 artists before scanning the full list.
test_artists = artists
concerts = {}
failures = 0

for number, artist in enumerate(test_artists, 1):
    name = artist["name"]
    print(f"Checking {number}/{len(test_artists)}: {name}")

    encoded_name = urllib.parse.quote(name, safe="")
    url = (
        "https://rest.bandsintown.com/artists/"
        + encoded_name
        + "/events?app_id=45"
    )

    try:
        request = urllib.request.Request(
            url,
            headers={"User-Agent": "PersonalConcertCalendar/1.0"}
        )
        with urllib.request.urlopen(
            request, timeout=20
        ) as response:
            events = json.load(response)

        if not isinstance(events, list):
            print("  Unexpected response; skipping")
            failures += 1
            continue

        for event in events:
            venue = event.get("venue") or {}
            city = (venue.get("city") or "").strip().lower()
            region = (venue.get("region") or "").strip().lower()
            country = (venue.get("country") or "").strip().lower()

            if (
                city in CITIES
                and region in {"utah", "ut", ""}
                and country in {"united states", "us", "usa"}
            ):
                event_id = str(
                    event.get("id")
                    or (name + event.get("datetime", "") + city)
                )

                if event_id not in concerts:
                    concerts[event_id] = {
                        "artist": name,
                        "date": event.get("datetime"),
                        "venue": venue.get("name"),
                        "city": venue.get("city"),
                        "url": event.get("url")
                    }

    except (
        urllib.error.URLError,
        ValueError,
        TimeoutError
    ) as error:
        failures += 1
        print("  Lookup failed:", error)

    time.sleep(1)

matches = sorted(
    concerts.values(),
    key=lambda e: e.get("date") or ""
)

with open("slc_concerts.json", "w") as file:
    json.dump(matches, file, indent=2)

print("\n-----------------------------")
print("Artists checked:", len(test_artists))
print("Lookup failures:", failures)
print("Local concerts found:", len(matches))
print("-----------------------------")

for concert in matches:
    print(
        concert["date"],
        "|", concert["artist"],
        "|", concert["venue"],
        "|", concert["city"]
    )

print("\nSaved results to slc_concerts.json")

