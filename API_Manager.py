import spotipy
from spotipy.oauth2 import SpotifyClientCredentials


class APIManager:
    """
        Class responsible for API queries.
    """
    def __init__(self):
        self.spotify = spotipy.Spotify(auth_manager=SpotifyClientCredentials())

    def find_art(self, album, artist):
        """
            Makes query to Spotify API based on album and artist names, and tries to extract url address of cover art.
        :param album: name of album
        :param artist: name of artist
        """
        query = f"{album} {artist}"

        result = self.spotify.search(q=query)

        try:
            return result['tracks']['items'][0]['album']['images'][0]['url']
        except IndexError:
            pass


