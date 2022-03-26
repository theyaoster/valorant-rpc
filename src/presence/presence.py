from InquirerPy.utils import color_print
import time, traceback, os, ctypes, asyncio, ssl

ssl_context = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
ssl_context.check_hostname = False
ssl_context.verify_mode = ssl.CERT_NONE

from ..content.content_loader import Loader
from ..localization.localization import Localizer
from .presences import (ingame,menu,startup,pregame)
from ..utilities.ystr_client import YstrClient

kernel32 = ctypes.WinDLL('kernel32')
user32 = ctypes.WinDLL('user32')
hWnd = kernel32.GetConsoleWindow()

class Presence:

    def __init__(self, config):
        self.config = config
        self.client = None
        self.saved_locale = None
        self.ystr_client = YstrClient(self.config)
        self.content_data = {}
    
    def main_loop(self):
        while True:
            presence_data = None
            try:
                presence_data = self.client.fetch_presence()
            except Exception: # If the game is closed
                self.ystr_client.offline()
                os._exit(1)

            if presence_data is not None:
                self.update_presence(presence_data["sessionLoopState"],presence_data)
            else:
                self.ystr_client.offline()
                os._exit(1)

            if Localizer.locale != self.saved_locale:
                self.saved_locale = Localizer.locale
                self.content_data = Loader.load_all_content(self.client)
            time.sleep(Localizer.get_config_value("presence_refresh_interval"))


    def init_loop(self):
        try:
            self.content_data = Loader.load_all_content(self.client)
            color_print([("LimeGreen bold", Localizer.get_localized_text("prints","presence","presence_running"))])
            presence_data = self.client.fetch_presence()

            if presence_data is not None:
                self.update_presence(presence_data["sessionLoopState"],presence_data)
                
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

            self.main_loop()

        except Exception as e:
            user32.ShowWindow(hWnd, 1)
            kernel32.SetConsoleMode(kernel32.GetStdHandle(-10), (0x4|0x80|0x20|0x2|0x10|0x1|0x40|0x100))
            color_print([("Red bold",Localizer.get_localized_text("prints","errors","error_message"))])
            traceback.print_exc()
            input(Localizer.get_localized_text("prints","errors","exit"))
            self.ystr_client.offline()
            os._exit(1)

    def update_presence(self,ptype,data=None):
        presence_types = {
            "startup": startup,
            "MENUS": menu,
            "PREGAME": pregame,
            "INGAME": ingame,
        }
        if ptype in presence_types.keys():
            presence_types[ptype].presence(self.ystr_client,client=self.client,data=data,content_data=self.content_data,config=self.config)