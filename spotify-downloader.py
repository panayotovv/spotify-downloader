import yt_dlp
from requests.auth import HTTPBasicAuth
import requests
import re
import os
from dotenv import load_dotenv

def loop_through_tracks(url, headers, params=None):
    tracks = []

    if params is None:
        params = {'limit': 20, 'offset': 0}

    while True:
        response = requests.get(url, headers=headers, params=params)
        response.raise_for_status()
        data = response.json()

        for item in data['items']:
            track_data = item.get('track', item)

            if not track_data:
                continue

            song_name = track_data.get('name')
            if not song_name:
                continue

            artist_names = [artist['name'] for artist in track_data.get('artists', [])]
            tracks.append({
                'track': song_name,
                'artists': artist_names
            })

        if data.get('next') is None:
            break
        params['offset'] += params['limit']

    return tracks


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
        artist_names = [artist['name'] for artist in data.get('artists', [])]
        song_name = data.get('name')

        return {'track': song_name, 'artists': artist_names}
    elif response.status_code == 400:
        raise requests.HTTPError(f'{response.text}')
    else:
        response.raise_for_status()


def get_spotify_album_tracks(album_id, access_token):
    headers = {
        'Authorization': f'Bearer {access_token}'
    }

    album_id = extract_spotify_id(album_id)

    album_url = f'https://api.spotify.com/v1/albums/{album_id}/'
    response = requests.get(album_url, headers=headers)
    response.raise_for_status()
    data = response.json()
    album_name = data['name']

    tracks_url = f'https://api.spotify.com/v1/albums/{album_id}/tracks'

    tracks = loop_through_tracks(tracks_url, headers)
    return album_name, tracks


def get_spotify_playlist_tracks(playlist_id, access_token):
    headers = {
        'Authorization': f'Bearer {access_token}'
    }

    playlist_id = extract_spotify_id(playlist_id)

    tracks_url = f'https://api.spotify.com/v1/playlists/{playlist_id}/tracks'
    playlist_url = f'https://api.spotify.com/v1/playlists/{playlist_id}/'

    params = {
        'limit': 100,
        'offset': 0
    }

    response = requests.get(playlist_url, headers=headers, params=params)
    response.raise_for_status()
    data = response.json()
    playlist_name = data['name']


    tracks = loop_through_tracks(tracks_url, headers, params)

    return playlist_name, tracks


def download_mp3(track_name, folder_path="."):
    os.makedirs(folder_path, exist_ok=True)

    ydl_opts = {
        'format': 'bestaudio/best',
        'outtmpl': os.path.join(folder_path, f'{safe_filename(track_name)}.%(ext)s'),
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
    load_dotenv()
    client_id = os.environ.get('CLIENT_ID')
    client_secret = os.environ.get('CLIENT_SECRET')
    spotify_url = ''

    try:
        access_token = get_access_token(client_id, client_secret)

        if 'playlist' in spotify_url:
            print('Playlist detected\n')
            playlist_name, tracks = get_spotify_playlist_tracks(spotify_url, access_token)
            folder_name = safe_filename(playlist_name)
        elif 'album' in spotify_url:
            print('Album detected\n')
            album_name, tracks = get_spotify_album_tracks(spotify_url, access_token)
            folder_name = safe_filename(album_name)
        else:
            print('Single track detected\n')
            track = get_spotify_track(spotify_url, access_token)
            tracks = [track]
            folder_name = safe_filename(track['track'])

        os.makedirs(folder_name, exist_ok=True)

        print(f'Found {len(tracks)} tracks\n')

        for i, track_name in enumerate(tracks, 1):
            print(f'[{i}/{len(tracks)}] Downloading: {track_name}')
            artist_str = ", ".join(track_name['artists'])
            song_str = track_name['track']
            full_name = f"{artist_str} - {song_str}"
            download_mp3(full_name, folder_path=folder_name)
            print('Done\n')

    except Exception as e:
        print(f'Error: {e}')


if __name__ == '__main__':
    main()



