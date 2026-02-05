import yt_dlp
from requests.auth import HTTPBasicAuth
import requests
import re
import os

def safe_filename(name):
    return re.sub(r'[\\/*?:"<>|]', '', name)


def get_access_token(client_id, client_secret):
    url = 'https://accounts.spotify.com/api/token'
    body_params = {
        'grant_type': 'client_credentials'
    }

    response = requests.post(
        url,
        data=body_params,
        auth=HTTPBasicAuth(client_id, client_secret)
    )
    if response.status_code == 200:
        return response.json()['access_token']
    elif response.status_code == 400:
        raise requests.HTTPError(f'{response.text}')
    else:
        response.raise_for_status()

def extract_spotify_id(url):
    return url.split('/')[-1].split('?')[0]


def get_spotify_track(track_id, access_token):
    headers = {
        'Authorization': f'Bearer {access_token}'
    }

    track_id = extract_spotify_id(track_id)

    url = f'https://api.spotify.com/v1/tracks/{track_id}'

    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        data = response.json()
        artist_name = data['artists'][0]['name']
        song_name = data['name']
        return f'{artist_name} - {song_name}'
    elif response.status_code == 400:
        raise requests.HTTPError(f'{response.text}')
    else:
        response.raise_for_status()


def get_spotify_playlist_tracks(playlist_id, access_token):
    headers = {
        'Authorization': f'Bearer {access_token}'
    }

    playlist_id = extract_spotify_id(playlist_id)

    url = f'https://api.spotify.com/v1/playlists/{playlist_id}/tracks'
    params = {
        'limit': 100,
        'offset': 0
    }

    tracks = []

    while True:
        response = requests.get(url, headers=headers, params=params)
        response.raise_for_status()
        data = response.json()

        for item in data['items']:
            track = item.get('track')
            if not track:
                continue

            artist_name = track['artists'][0]['name']
            song_name = track['name']
            tracks.append(f'{artist_name} - {song_name}')

        if data['next'] is None:
            break

        params['offset'] += params['limit']

    return tracks


def download_mp3(track_name):
    ydl_opts = {
        'format': 'bestaudio/best',
        'outtmpl': f'{safe_filename(track_name)}.%(ext)s',
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        }],
        'quiet': False,
        'no_warnings': True,
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        ydl.download([f'ytsearch1:{track_name} official audio'])


def main():
    client_id = os.environ.get('CLIENT_ID')
    client_secret = os.environ.get('CLIENT_SECRET')
    spotify_url = 'https://open.spotify.com/track/4IO2X2YoXoUMv0M2rwomLC'

    try:
        access_token = get_access_token(client_id, client_secret)

        if 'playlist' in spotify_url:
            print('Playlist detected\n')
            tracks = get_spotify_playlist_tracks(spotify_url, access_token)
        else:
            print('Single track detected\n')
            tracks = [get_spotify_track(spotify_url, access_token)]

        print(f'Found {len(tracks)} tracks\n')

        for i, track_name in enumerate(tracks, 1):
            print(f'[{i}/{len(tracks)}] Downloading: {track_name}')
            download_mp3(track_name)
            print('Done\n')

    except Exception as e:
        print(f'Error: {e}')


if __name__ == '__main__':
    main()



