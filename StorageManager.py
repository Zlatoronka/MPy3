import sqlite3
from mutagen.mp3 import MP3
from mutagen.id3 import ID3
import time
import zlib
from kivymd.toast import toast


class StorageManager:
    """
        Class responsible for interactions with database.
    """
    def __init__(self):
        self.records = []

    def writing_songs_to_database(self):
        """
            Checking if hash value of song we would like to write in database exists and if not writes all the data
            (ID3 tags plus song length, path, calculated crc32 value of the song) to database.
        """
        connection = sqlite3.connect('playlists.db')
        cursor = connection.cursor()
        cursor.execute("""SELECT path FROM songs""")
        songs_present_in_database = cursor.fetchall()
        songs_present_in_database = [s[0] for s in songs_present_in_database]

        query = """INSERT INTO songs (title, album, artist, genre, raw_length, converted_length, path, hash_value) 
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)"""
        for record in self.records:
            if record[6] not in songs_present_in_database:
                cursor.execute(query,
                               (record[0], record[1], record[2], record[3], record[4], record[5], record[6], record[7]))
        connection.commit()
        connection.close()
        self.records.clear()

    def song_info_extraction(self, audio_path):
        """
            Extracts ID3 tags from MP3s, creates hash values of each song based on these tags and converts length of the
            song in format 00:00.
        :param audio_path: path to mp3 file
        """
        for song in audio_path:
            try:
                info = MP3(song, ID3=ID3)
                converted_time = time.strftime('%M:%S', time.gmtime(info.info.length))
                hash_value = zlib.crc32(bytes(
                    f"{info.tags['TIT2'].text[0]}{info.tags['TALB'].text[0]}{info.tags['TPE1'].text[0]}{info.tags['TCON'].text[0]}",
                    'utf-8'))
                self.records.append(
                    (info.tags['TIT2'].text[0], info.tags['TALB'].text[0], info.tags['TPE1'].text[0],
                     info.tags['TCON'].text[0], int(info.info.length), converted_time, song, hash_value))
            except KeyError:
                toast('Some of the songs have missing tags!\nFix them before import!',
                      background=[0.6745, 0.2941, 0.5059, 0.7])
        self.writing_songs_to_database()

    @staticmethod
    def check_for_path_changed(hash_value, s_id):
        """
            Checks if there is different song record of same song.
        :param hash_value: hash value of song to be queried in database
        :param s_id:  song id of song to be queried in database
        :return: record with matching hash value if there is such with different song id.
        """
        connection = sqlite3.connect('playlists.db')
        cursor = connection.cursor()
        cursor.execute("""SELECT * FROM songs WHERE hash_value=? AND s_id != ?""", (hash_value, s_id))
        return cursor.fetchone()

    @staticmethod
    def get_songs_from_database(f_spinner, f_text, s_spinner, s_text):
        """
            Fetch song information from database, based on values passed from user input.
        :param f_spinner: first_spinner value from SecondScreen
        :param f_text: first_text_input value from SecondScreen
        :param s_spinner: second_spinner value from SecondScreen
        :param s_text: second_text_input value from SecondScreen
        :return: songs data
        """
        connection = sqlite3.connect('playlists.db')
        cursor = connection.cursor()
        try:
            if ((f_spinner != 'Query Condition') and f_text) and ((s_spinner != 'Query Condition') and s_text):
                query = f"SELECT * FROM songs WHERE {f_spinner} LIKE '%{f_text}%' and {s_spinner} LIKE '%{s_text}%'"

            elif (f_spinner != 'Query Condition') and f_text:
                query = f"SELECT * FROM songs WHERE {f_spinner} LIKE '%{f_text}%'"

            elif (s_spinner != 'Query Condition') and s_text:
                query = f"SELECT * FROM songs WHERE {s_spinner} LIKE '%{s_text}%'"

            cursor.execute(query)
            return cursor.fetchall()
        except:
            # Do nothing if there is not defined query
            pass

    @staticmethod
    def delete_song_from_database(s_id):
        """
            Deletes song CASCADE from database.
        :param s_id:
        :return:
        """
        connection = sqlite3.connect('playlists.db')
        connection.execute("PRAGMA foreign_keys = 1")
        cursor = connection.cursor()
        query = """DELETE FROM songs WHERE s_id = ?"""
        cursor.execute(query, (s_id,))
        connection.commit()
        connection.close()

    @staticmethod
    def get_playlists_from_database():
        """
            Fetches data for records in playlist table in database.
        :return: tuples of playlist ids and playlist names
        """
        connection = sqlite3.connect('playlists.db')
        cursor = connection.cursor()
        cursor.execute("""SELECT p_id, playlist FROM playlists""")
        return cursor.fetchall()

    @staticmethod
    def get_playlist_songs_from_database(p_id):
        """
            Fetches playlist record based on playlist id.
        :param p_id: playlist id
        :return: tuples of all songs present in concrete playlist
        """
        connection = sqlite3.connect('playlists.db')
        cursor = connection.cursor()
        query = """SELECT s.s_id, s.title, s.album, s.artist, s.genre, s.raw_length, s.converted_length, s.path, 
        s.hash_value FROM songs s INNER JOIN playlist_songs ps on s.s_id = ps.s_id WHERE p_id=?"""
        cursor.execute(query, (p_id,))
        return cursor.fetchall()

    @staticmethod
    def delete_playlist_from_database(p_id):
        """
            Deletes playlist CASCADE from database.
        :param p_id:
        :return:
        """
        connection = sqlite3.connect('playlists.db')
        connection.execute("PRAGMA foreign_keys = 1")
        cursor = connection.cursor()
        query = """DELETE FROM playlists WHERE p_id = ?"""
        cursor.execute(query, (p_id,))
        connection.commit()
        connection.close()

    @staticmethod
    def create_playlist(name, song_ids):
        """
            Makes record in playlist table in database after that takes p_id of the playlists and makes records in
            playlist_songs junction table based on song ids extracted in song_ids container of SongManager class.
        :param name: name of playlist to be created
        :param song_ids: list of all song ids to be added in current playlist
        :return:
        """
        connection = sqlite3.connect('playlists.db')
        cursor = connection.cursor()
        query = """INSERT INTO playlists (playlist) VALUES (?)"""
        cursor.execute(query, (name,))
        connection.commit()

        cursor.execute(f"SELECT p_id FROM playlists where playlist=='{name}'")
        playlist_id = cursor.fetchone()
        playlist_id = playlist_id[0]

        for s_id in song_ids:
            cursor.execute(f"INSERT INTO playlist_songs (p_id, s_id) VALUES (?, ?)", (playlist_id, s_id))

        connection.commit()
        connection.close()


def create_data_base():
    """
        Creates schema of playlist database.
    """
    connection = sqlite3.connect('playlists.db')
    cursor = connection.cursor()

    cursor.execute("""DROP TABLE playlist_songs""")
    cursor.execute("""DROP TABLE playlists""")
    cursor.execute("""DROP TABLE songs""")
    connection.commit()

    cursor.execute("""CREATE TABLE IF NOT EXISTS playlists (
                    p_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    playlist TEXT NOT NULL
                        )""")

    connection.commit()

    cursor.execute("""CREATE TABLE IF NOT EXISTS songs (
                    s_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    title TEXT NOT NULL,
                    album TEXT NOT NULL,
                    artist TEXT NOT NULL,
                    genre TEXT NOT NULL,
                    raw_length INTEGER NOT NULL,
                    converted_length TEXT NOT NULL,
                    path TEXT NOT NULL,
                    hash_value INTEGER NOT NULL
                    )""")

    connection.commit()

    cursor.execute("""CREATE TABLE IF NOT EXISTS playlist_songs(
                    p_id INTEGER,
                    s_id INTEGER,
                    FOREIGN KEY (p_id) REFERENCES playlists (p_id) ON DELETE CASCADE,
                    FOREIGN KEY (s_id) REFERENCES songs (s_id) ON DELETE CASCADE

                    )""")

    connection.commit()
    connection.close()


# if __name__ == '__main__':
#     create_data_base()
