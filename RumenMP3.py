import pygame
from kivy.lang import Builder
from kivy.core.window import Window
from kivy.clock import Clock
from kivy.config import Config
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.metrics import dp
from kivymd.uix.filemanager import MDFileManager
from kivymd.uix.list import OneLineAvatarIconListItem, TwoLineAvatarIconListItem, IconLeftWidget, IconRightWidget
from kivymd.toast import toast
from kivymd.app import MDApp
from pygame import mixer
from SongManager import SongManager
from StorageManager import StorageManager
from colors import colors
import random
import time
import os


class MainScreen(Screen):
    mixer.init()

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self.if_art_not_called = True
        self.is_playing = False
        self.muted = False
        self.loop_same_song = False
        self.playlist_index = 0
        self.volume_level = 0.3
        self.converted_song_length = ""
        self.raw_song_length = 0
        self.song_manager = SongManager()
        self.current_position = 0
        Clock.schedule_once(lambda dt: self.create_playlist_items())
        Clock.schedule_interval(self.move_label, 1 / 60)

    def call_api(self):
        """
            Tries to extract album art form Spotify API based on artist name and album name of current played song.
            If not successfully sets default image. If query to API returns None, sets default image.
        """
        try:
            if self.if_art_not_called:
                try:
                    album = self.song_manager.song_list[self.playlist_index].album
                    artist = self.song_manager.song_list[self.playlist_index].artist
                    image = self.song_manager.api.find_art(album=album, artist=artist)
                    self.ids.cover_image.source = image
                    self.if_art_not_called = False
                except IndexError:
                    toast("No song loaded!", background=[0.6745, 0.2941, 0.5059, 0.7])

            else:
                self.ids.cover_image.source = 'icons/music_note.png'
                self.if_art_not_called = True
        except ValueError:
            self.ids.cover_image.source = 'icons/music_note.png'
            self.if_art_not_called = True

    def populate_playlist(self, p_id=None, first_spinner=None, first_text_input=None, second_spinner=None,
                          second_text_input=None):

        """
            Extracts information about songs based on values placed by user. Populates playlist with list items based
            on songs objects.
        :param p_id: playlist id value
        :param first_spinner: first_spinner value from SecondScreen
        :param first_text_input: first_text_input value from SecondScreen
        :param second_spinner: second_spinner value from SecondScreen
        :param second_text_input: second_text_input value from SecondScreen
        :return:
        """
        self.song_manager.create_song_objects(p_id, first_spinner, first_text_input, second_spinner,
                                              second_text_input)
        self.ids.playlist.clear_widgets()
        self.generate_songlist_items()

    def generate_songlist_items(self, *args):
        """
            Creates list items with information of songs objects in song_list of SongManager
        """
        for index, song in enumerate(self.song_manager.song_list):
            left_icon = IconLeftWidget(icon="icons/music_note.png", user_font_size=dp(12))

            right_icon = IconRightWidget(icon="icons/delete.png",
                                         on_press=lambda x, i=index: self.remove_from_songlist(i),
                                         user_font_size=dp(12))

            list_item = TwoLineAvatarIconListItem(text=f"[font=fonts/Roboto-Bold]{song.title}[/font]",
                                                  secondary_text=f"[font=fonts/Roboto-Bold.ttf]{song.artist} - {song.album}[/font]",
                                                  on_release=lambda x, i=index, t=song.title: self.play_from_list_item(
                                                      i, t))
            list_item.add_widget(left_icon)
            list_item.add_widget(right_icon)
            self.ids.playlist.add_widget(list_item)

    def create_playlist_items(self):
        """
            Takes info from database about present playlists and populates playlist list in SecondScreen.
        """
        self.manager.get_screen('second').ids.playlists_to_manage.clear_widgets()
        self.song_manager.create_playlist_objects()
        for index, playlist in enumerate(self.song_manager.playlist_list):
            left_icon = IconLeftWidget(icon="icons/playlist.png", user_font_size=dp(12))

            right_icon = IconRightWidget(icon="icons/delete.png",
                                         on_press=lambda x, pid=playlist.p_id: self.delete_playlist(pid),
                                         user_font_size=dp(12))

            list_item = OneLineAvatarIconListItem(text=f"[font=fonts/Roboto-Bold]{playlist.name}[/font]",
                                                  on_press=lambda x, pid=playlist.p_id: self.populate_playlist(pid),
                                                  on_release=lambda x: self.change_screen())
            list_item.add_widget(left_icon)
            list_item.add_widget(right_icon)
            self.manager.get_screen('second').ids.playlists_to_manage.add_widget(list_item)

    def remove_from_songlist(self, index):
        """
            Removes song object from SongManager`s song_list by passed index.
        :param index: song_list index to be popped.
        """
        self.ids.playlist.clear_widgets()
        self.song_manager.song_list.pop(index)
        self.generate_songlist_items()

    def change_screen(self):
        """
            When triggered, changes screen to main.
        """
        self.manager.current = 'main'
        self.manager.transition.direction = 'right'

    def delete_playlist(self, p_id):
        """
            Deletes playlist from database, based on playlist id parameter.
        :param p_id: playlist id to be deleted.
        """
        self.song_manager.storage.delete_playlist_from_database(p_id)
        self.create_playlist_items()

    def play_from_list_item(self, index, title):
        """
            On list item click plays clicked song.
        :param index: index of the song in SongManages song_list
        :param title: title of the song
        """
        toast(title, background=[0.6745, 0.2941, 0.5059, 0.7])
        self.playlist_index = index
        mixer.music.stop()
        mixer.music.unload()
        Clock.unschedule(self.progress_slider_update)
        self.current_position = 0
        self.is_playing = False
        self.play()

    def save_playlist(self, name):
        """
            Creates playlist object based on song objects currently in SongManager`s song list.
        :param name: name of playlist to be created.
        """
        toast(name, background=[0.6745, 0.2941, 0.5059, 0.7])
        self.song_manager.getting_s_ids_from_song_list()
        self.song_manager.storage.create_playlist(name, self.song_manager.song_ids)
        self.song_manager.create_playlist_objects()
        self.create_playlist_items()

    def shuffle(self):
        """
            Clears playlist, shuffles song_list and repopulate playlist.
        """
        self.ids.playlisokt.clear_widgets()
        self.ids.shuffle_button.icon = 'icons/shuffle.png'
        random.shuffle(self.song_manager.song_list)
        self.playlist_index = -1
        self.generate_songlist_items()

    def loop_one(self):
        """
            If loop flag is true sets it to false else sets it to true.
        """
        if self.loop_same_song:
            self.loop_same_song = False
            self.ids.loop_button.icon = 'icons/no_loop.png'

        else:
            self.loop_same_song = True
            self.ids.loop_button.icon = 'icons/loop.png'

    def clear_songs_from_list(self):
        """
            Clears songlist widgets from playlist and clears song_list of SongManager class.
        """
        self.ids.playlist.clear_widgets()
        self.song_manager.song_list.clear()

    def prev_next(self, command):
        """
            Stopes and unload current played song. Sets position of progress bar slider to 0. Checks if looping one song
            is active and if it is continues to play the same song. If previous button is pressed loads previous song
            object in song_list, else loads next object. If index is greater than length of song_lists plays first song,
            if is less than 0 plays last song.
        :param command: value passed by previous/next buttons of MainScreen.

        """
        mixer.music.stop()
        mixer.music.unload()
        Clock.unschedule(self.progress_slider_update)
        self.current_position = 0
        self.is_playing = False
        if self.loop_same_song:
            pass

        else:
            if command == 'prev':
                self.playlist_index -= 1
            elif command == 'next':
                self.playlist_index += 1

        if self.playlist_index >= len(self.song_manager.song_list):
            self.playlist_index = 0
        elif self.playlist_index < 0:
            self.playlist_index = len(self.song_manager.song_list) - 1
        self.play()

    def load(self, index):
        """
            First unload current song and loads song object contained in song_list of SongManager instance
             by passed index. Extracts information about song length and its converted value in format of '00:00' from
             songs objects.
        :param index: index of the song object in SongManager song_list
        :return:
        """
        mixer.music.unload()
        self.converted_song_length = self.song_manager.song_list[index].converted_length
        self.raw_song_length = self.song_manager.song_list[index].raw_length
        mixer.music.load(self.song_manager.song_list[index].path)

    def move_label(self, dt):
        """
            Makes song info label to move.
        :param dt:
        :return:
        """
        info_label = self.manager.get_screen('main').ids.info_label
        info_label.x -= 1
        if info_label.x < -(info_label.parent.width/2 + info_label.texture_size[0]/2):
            info_label.x = info_label.parent.width/2 + info_label.texture_size[0]/2

    def progress_slider_update(self, *args):
        """
            First sets max value of progress bar slider, after which sets labels showing song length and current playing
            position. Position is updating every second by 1. If slider current position is equal to its max value
            triggers prev_next method as one time event.
        """

        self.current_position += 1
        self.ids.progress_slider.value = self.current_position
        self.ids.progress_slider.max = self.raw_song_length
        self.ids.time_played_label.text = time.strftime('%M:%S', time.gmtime(self.current_position))
        if self.current_position >= self.ids.progress_slider.max:
            Clock.create_trigger(self.prev_next("next"))

    def play(self, *args):
        """
            If music playing pauses it. If music not playing checks current position of progress bar slider and if
            this value is greater than 0 resumes playing song from this position else starts new song.
        """
        if self.is_playing:
            self.is_playing = False
            self.ids.play_button.icon = 'icons/play.png'
            mixer.music.pause()
            Clock.unschedule(self.progress_slider_update)

        else:
            self.ids.play_button.icon = 'icons/pause.png'
            if self.current_position != 0:
                self.is_playing = True
                mixer.music.unpause()
                Clock.schedule_interval(self.progress_slider_update, 1)

            else:
                try:
                    self.load(self.playlist_index)
                    self.ids.info_label.text = f"{self.song_manager.song_list[self.playlist_index].title} by " \
                                               f"{self.song_manager.song_list[self.playlist_index].artist}"
                    toast(self.song_manager.song_list[self.playlist_index].title,
                          background=[0.6745, 0.2941, 0.5059, 0.7])
                    Clock.schedule_interval(self.progress_slider_update, 1)
                    self.ids.song_duration_label.text = self.converted_song_length
                    self.ids.progress_slider.max = self.raw_song_length
                    self.is_playing = True
                    if self.muted:
                        pass
                    else:
                        mixer.music.set_volume(self.volume_level)
                    mixer.music.play()
                except IndexError:
                    # if there are no song to play do nothing
                    pass

                except pygame.error:
                    try:
                        hash_value = self.song_manager.song_list[self.playlist_index].hash_value
                        song_id = self.song_manager.song_list[self.playlist_index].s_id
                        self.playlist_index = self.song_manager.repair_current_playlist(hash_value, song_id)
                        self.play()
                    except:
                        toast("File not found! Go next!", background=[0.6745, 0.2941, 0.5059, 0.7])
                        self.playlist_index -= 1
                    finally:
                        self.ids.playlist.clear_widgets()
                        self.generate_songlist_items()

    def mute(self, volume_button_widget):
        """
            Mutes volume if not muted and unmute it if muted.
        :param volume_button_widget: volume button from MainScreen
        """
        if self.muted:
            self.muted = False
            volume_button_widget.icon = 'icons/volume.png'
            mixer.music.set_volume(self.volume_level)

        else:
            self.muted = True
            volume_button_widget.icon = 'icons/mute.png'
            mixer.music.set_volume(0)

    def change_volume(self, volume_slider_widget):
        """
            Changes volume based on slider value. Mute sound if value reaches 0.
        :param volume_slider_widget: volume slider widget from MainScreen
        """
        self.volume_level = volume_slider_widget.value
        mixer.music.set_volume(self.volume_level)

        if self.volume_level:
            self.muted = False
            self.ids.volume_button.icon = 'icons/volume.png'
        else:
            self.muted = True
            self.ids.volume_button.icon = 'icons/mute.png'


class SecondScreen(Screen):

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self.manager_open = False
        self.directory = ""
        self.songs_paths = []
        self.storage = StorageManager()
        self.file_manager = MDFileManager(
            exit_manager=self.exit_manager,
            select_path=self.select_path,
        )

    def file_manager_open(self):
        """
            Opens file_manager in path set in show method.
        :return:
        """
        self.file_manager.show(r'D:\Музика')
        self.manager_open = True

    def exit_manager(self, *args):
        """
            If there is valid path, file_manager passes list with all paths to song_info_extraction method of
            StorageManager class, after which file_manager closes.
        """
        if self.songs_paths:
            # takes list of songs paths and send them for processing in StorageManager class
            self.storage.song_info_extraction(self.songs_paths)
            self.songs_paths.clear()
        self.manager_open = False
        self.file_manager.close()

    def select_path(self, path):
        """
        It will be called when you click on the file name
        of the catalog selection button.

        :param path: path to the selected directory or file;
        """
        self.directory = path
        if os.path.isdir(self.directory):
            self.songs_paths.clear()
            for song in os.listdir(self.directory):

                if song[-3:] == 'mp3':
                    self.songs_paths.append(f"{self.directory}/{song}")

        else:
            if self.directory[-3:] == 'mp3':
                self.songs_paths.append(self.directory)
        toast(self.directory, background=[0.6745, 0.2941, 0.5059, 0.7])
        self.exit_manager()


class WindowManager(ScreenManager):
    pass


class MPy3PlayerApp(MDApp):
    Window.size = (400, 700)
    Window.minimum_width = 250
    Window.minimum_height = 350
    Config.set('input', 'mouse', 'mouse,multitouch_on_demand')

    def build(self):
        self.theme_cls.colors = colors
        self.theme_cls.primary_palette = 'Pink'
        self.theme_cls.primary_hue = '200'

        return Builder.load_file('RumenMP3.kv')


if __name__ == "__main__":
    MPy3PlayerApp().run()
