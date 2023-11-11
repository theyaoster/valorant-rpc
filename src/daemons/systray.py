import os, os.path, urllib.request, sys, time
from PIL import Image
from pystray import Icon, Menu, MenuItem
from InquirerPy.utils import color_print

from ..utility_functions import Filepath, ConsoleWindow
from ..config.config_editor import ConfigEditor
from ..localization.localization import Localizer
from ..config.constants import Constants

ICON_FILEPATH = Filepath.get_path(os.path.join(Filepath.get_appdata_folder(), Constants.ICON_FILENAME))

# Maintains systray icon with menu
class Systray:

    def __init__(self, client, config):
        self.client = client
        self.config = config

    def run(self):
         # Fetch Icon from URL
        if not os.path.isfile(ICON_FILEPATH):
            urllib.request.urlretrieve(Constants.ICON_URI, ICON_FILEPATH)

        systray_image = Image.open(ICON_FILEPATH)
        systray_menu = Menu(
            MenuItem('Show Window', ConsoleWindow.toggle, checked=lambda _: ConsoleWindow.visible),
            MenuItem('Edit Settings', self.modify_config),
            MenuItem('Restart', self.restart),
            MenuItem('Exit', self.exit)
        )
        self.systray = Icon(Constants.PROGRAM_NAME, systray_image, Constants.PROGRAM_NAME, systray_menu)
        self.systray.run()

    def exit(self):
        self.systray.stop()
        os._exit(1)

    def modify_config(self):
        ConsoleWindow.show()
        ConfigEditor()
        color_print([("LimeGreen", f"{Localizer.get_localized_text('prints', 'systray', 'hiding_window')}\n")])
        time.sleep(5)
        ConsoleWindow.hide()

    def restart(self):
        ConsoleWindow.show()
        os.system('cls' if os.name == 'nt' else 'clear')
        os.execl(sys.executable, os.path.abspath(__file__), *sys.argv)

