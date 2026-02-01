import yt_dlp
from requests.auth import HTTPBasicAuth
import requests


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


def get_spotify_track(track_id, access_token):
    headers = {
        'Authorization': f'Bearer {access_token}'
    }
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


def get_youtube_link(track_name, youtube_api_key):
    url = 'https://www.googleapis.com/youtube/v3/search'
    params = {
        'part': 'snippet',
        'q': track_name,
        'type': 'video',
        'maxResults': 1,
        'key': youtube_api_key
    }

    response = requests.get(url, params=params)
    response.raise_for_status()
    data = response.json()

    if not data['items']:
        return None

    video_id = data['items'][0]['id']['videoId']
    return f'https://www.youtube.com/watch?v={video_id}'


def download_mp3(youtube_url, track_name):
    ydl_opts = {
        'format': 'bestaudio/best',
        'outtmpl': f'{track_name}.%(ext)s',
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        }],
        'quiet': False,
        'no_warnings': True,
        'jsruntimes': 'node:/usr/local/bin/node'
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        ydl.download([youtube_url])



def main():
    client_id = 'YOUR_SPOTIFY_CLIENT_ID'
    client_secret = 'YOUR_SPOTIFY_CLIENT_SECRET'
    track_id = 'YOUR_SPOTIFY_TRACK_ID'
    youtube_api_key = 'YOUR_YOUTUBE_API_KEY'

    try:
        access_token = get_access_token(client_id, client_secret)
        track_name = get_spotify_track(track_id, access_token)
        print(f'\nTrack found: {track_name}')

        youtube_url = get_youtube_link(track_name, youtube_api_key)
        if not youtube_url:
            print('No YouTube video found for this track.')
            return
        print(f'YouTube URL: {youtube_url}\n')

        print('Downloading MP3...')
        download_mp3(youtube_url, track_name)
        print('Download complete!')

    except Exception as e:
        print(f'An error occurred: {e}')

if __name__ == '__main__':
    main()
