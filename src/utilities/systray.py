from PIL import Image
from pystray import Icon, Menu, MenuItem
import ctypes, os, urllib.request, sys, time
from InquirerPy.utils import color_print

from .filepath import Filepath
from .config.modify_config import ConfigEditor
from ..localization.localization import Localizer
from ..presence.presence_utilities import Utilities

ICON_URI = "https://raw.githubusercontent.com/theyaoster/valorant-ystr/master/favicon.ico"
ICON_FILENAME = "favicon.ico"
ICON_FILEPATH = Filepath.get_path(os.path.join(Filepath.get_appdata_folder(), ICON_FILENAME))

class Systray:

    def __init__(self, client, config):
        self.client = client
        self.config = config
        self.user = ctypes.WinDLL('user32')
        self.kernel = ctypes.WinDLL('kernel32')
        self.window = self.kernel.GetConsoleWindow()
        self.visible = False

    def run(self):
        self.generate_icon()
        systray_image = Image.open(ICON_FILEPATH)
        systray_menu = Menu(
            MenuItem('Show Window', self.tray_window_toggle, checked=lambda _: self.visible),
            MenuItem('Edit Settings', self.modify_config),
            MenuItem('Restart', self.restart),
            MenuItem('Exit', self.exit)
        )
        self.systray = Icon("VALORANT-ystr", systray_image, "VALORANT-ystr", systray_menu)
        self.systray.run()

    def exit(self):
        self.systray.stop()
        os._exit(1)

    def generate_icon(self):
        urllib.request.urlretrieve(ICON_URI, ICON_FILEPATH)

    def modify_config(self):
        self.show()
        ConfigEditor()
        if not self.visible:
            color_print([("LimeGreen", f"{Localizer.get_localized_text('prints', 'systray', 'hiding_window')}\n")])
            time.sleep(5)
            self.hide()

    def restart(self):
        self.user.ShowWindow(self.window, 1)
        os.system('cls' if os.name == 'nt' else 'clear')
        os.execl(sys.executable, os.path.abspath(__file__), *sys.argv)

    def tray_window_toggle(self):
        self.visible = not self.visible
        self.user.ShowWindow(self.window, int(self.visible))

    def show(self):
        self.user.ShowWindow(self.window, 1)

    def hide(self):
        self.user.ShowWindow(self.window, 0)
