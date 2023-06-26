from StorageManager import StorageManager
from API_Manager import APIManager


class Song:
    """
        Class responsible for creation of Song objects.
    """
    def __init__(self, s_id, title, album, artist, genre, raw_length, converted_length, path, hash_value):
        self.s_id = s_id
        self.title = title
        self.album = album
        self.artist = artist
        self.genre = genre
        self.raw_length = raw_length
        self.converted_length = converted_length
        self.path = path
        self.hash_value = hash_value

    def __str__(self):
        return self.title


class Playlist:
    """
        Class responsible for creation of playlist and songs objects.
    """
    def __init__(self, p_id, name):
        self.p_id = p_id
        self.name = name

    def __str__(self):
        return f"{self.name} id: {self.p_id}"


class SongManager:
    """
        Class responsible for managing playlists.
    """
    def __init__(self):
        self.song_ids = []
        self.song_list = []
        self.playlist_list = []
        self.db_query = []
        self.storage = StorageManager()
        self.api = APIManager()

    def create_song_objects(self, p_id, f_spinner, f_text, s_spinner, s_text):
        """
            Creates song objects from saved playlist or from database queries.
        :param p_id: playlist id
        :param f_spinner: first spinner value of SecondScreen
        :param f_text: first text input value of SecondScreen
        :param s_spinner: second spinner value of SecondScreen
        :param s_text: second text input value of SecondScreen
        """

        try:
            self.db_query = []
            if p_id:
                self.db_query = self.storage.get_playlist_songs_from_database(p_id)
            else:
                self.db_query = self.storage.get_songs_from_database(f_spinner, f_text, s_spinner, s_text)
            for song in self.db_query:
                s = Song(s_id=song[0], title=song[1], album=song[2], artist=song[3], genre=song[4], raw_length=song[5],
                         converted_length=song[6], path=song[7], hash_value=song[8])
                self.song_list.append(s)
        except TypeError:
            # if there is no valid data from user input do nothing
            pass

    def getting_s_ids_from_song_list(self):
        """
            Gets song ids from song objects in song_list.
        """
        self.song_ids.clear()
        for song in self.song_list:
            self.song_ids.append(song.s_id)

    def repair_current_playlist(self, hash_value, s_id):
        """
            If path passed to pygame mixer load method is not valid, takes id and hash value of the song, pops song
            object from SongManager song_list with matching s_id, makes query to check if there is another record with
            same hash value in database and if such exists, inserts new song object on place of old one.
        :param hash_value: hash value of song object with invalid path
        :param s_id: song id of song object with invalid path
        :return:
        """
        index = 0
        for i, song in enumerate(self.song_list):
            if song.s_id == s_id:
                self.song_list.remove(song)
                index = i
        query = self.storage.check_for_path_changed(hash_value, s_id)
        s = Song(s_id=query[0], title=query[1], album=query[2], artist=query[3], genre=query[4], raw_length=query[5],
                 converted_length=query[6], path=query[7], hash_value=query[8])
        self.song_list.insert(index, s)
        return index

    def create_playlist_objects(self):
        """
            Creates playlist objects.
        """
        self.playlist_list.clear()
        playlist_query = self.storage.get_playlists_from_database()
        for pl in playlist_query:
            p = Playlist(p_id=pl[0], name=pl[1])
            self.playlist_list.append(p)

