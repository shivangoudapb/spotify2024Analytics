import requests
import pandas as pd
import time

# -----------------------------
# Spotify API credentials
# -----------------------------
client_id = "Your spotify client id"
client_secret = "Your Spotify client secret"

# -----------------------------
# Get access token
# -----------------------------
def get_token(client_id, client_secret):
    url = "https://accounts.spotify.com/api/token"
    response = requests.post(url, {
        'grant_type': 'client_credentials',
        'client_id': client_id,
        'client_secret': client_secret,
    })
    response.raise_for_status()
    return response.json()['access_token']

# -----------------------------
# Search track & get album image
# -----------------------------
def search_track(track_name, artist_name, token):
    query = f"{track_name} artist:{artist_name}"
    url = f"https://api.spotify.com/v1/search?q={query}&type=track&limit=1"
    response = requests.get(url, headers={
        'Authorization': f'Bearer {token}'
    })

    # Handle rate limiting
    if response.status_code == 429:
        retry_after = int(response.headers.get("Retry-After", 5))
        retry_after = min(retry_after, 30)
        print(f"⚠️ Rate limited. Sleeping {retry_after}s...")
        time.sleep(retry_after)
        return search_track(track_name, artist_name, token)

    if response.status_code != 200:
        print(f"❌ Search error {response.status_code}: {response.text[:100]}")
        return None, None

    try:
        item = response.json()['tracks']['items'][0]
        track_id = item['id']
        image_url = item['album']['images'][0]['url'] if item['album']['images'] else None
        return track_id, image_url
    except (KeyError, IndexError):
        return None, None

# -----------------------------
# Main: Load CSV & fetch images
# -----------------------------
# Make sure your CSV has at least "Track" and "Artist" columns
df = pd.read_csv("songs.csv", encoding="ISO-8859-1")


access_token = get_token(client_id, client_secret)

df["spotify_track_id"] = None
df["image_url"] = None

for i, row in df.iterrows():
    print(f"🔎 Processing: {row['Track']} - {row['Artist']}")
    track_id, image_url = search_track(row["Track"], row["Artist"], access_token)
    df.at[i, "spotify_track_id"] = track_id
    df.at[i, "image_url"] = image_url
    time.sleep(0.5)  # small delay to avoid hitting limits

# -----------------------------
# Save results to new CSV
# -----------------------------
df.to_csv("songs_with_images.csv", index=False)
print("✅ Done! File saved as songs_with_images.csv")
