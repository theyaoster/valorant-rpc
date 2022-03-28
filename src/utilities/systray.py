from PIL import Image
from pystray import Icon as icon, Menu as menu, MenuItem as item
import ctypes, os, urllib.request, sys, time
from InquirerPy.utils import color_print

from .error_handling import handle_error

from .filepath import Filepath
from .config.modify_config import Config_Editor
from ..localization.localization import Localizer
from ..presence.presence_utilities import Utilities

kernel32 = ctypes.WinDLL('kernel32')
user32 = ctypes.WinDLL('user32')
hWnd = kernel32.GetConsoleWindow()

window_shown = False

class Systray:

    def __init__(self, client, config):
        self.client = client
        self.config = config

    def run(self):
        global window_shown
        Systray.generate_icon()
        systray_image = Image.open(Filepath.get_path(os.path.join(Filepath.get_appdata_folder(), 'favicon.ico')))
        systray_menu = menu(
            item('Show Window', Systray.tray_window_toggle, checked=lambda _: window_shown),
            item('Edit Settings', Systray.modify_config),
            item('Restart', Systray.restart),
            item('Exit', self.exit)
        )
        self.systray = icon("VALORANT-ystr", systray_image, "VALORANT-ystr", systray_menu)
        self.systray.run()

    def exit(self):
        self.systray.visible = False
        self.systray.stop()
        os._exit(1)

    @staticmethod
    def generate_icon():
        urllib.request.urlretrieve('https://raw.githubusercontent.com/theyaoster/valorant-ystr/v2/favicon.ico',Filepath.get_path(os.path.join(Filepath.get_appdata_folder(),'favicon.ico')))

    @staticmethod
    def modify_config():
        user32.ShowWindow(hWnd, 1)
        Config_Editor()
        if not window_shown:
            color_print([("LimeGreen",f"{Localizer.get_localized_text('prints','systray','hiding_window')}\n")])
            time.sleep(1)
            user32.ShowWindow(hWnd, 0)

    @staticmethod
    def restart():
        user32.ShowWindow(hWnd, 1)
        os.system('cls' if os.name == 'nt' else 'clear')
        os.execl(sys.executable, os.path.abspath(__file__), *sys.argv)

    @staticmethod
    def tray_window_toggle(wrapper):
        global window_shown
        try:
            window_shown = not wrapper()
            if window_shown:
                user32.ShowWindow(hWnd, 1)
            else:
                user32.ShowWindow(hWnd, 0)
        except Exception:
            handle_error()