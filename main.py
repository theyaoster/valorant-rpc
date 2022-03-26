from InquirerPy.utils import color_print
import ctypes, os, traceback, colorama

from src.startup import Startup
from src.utilities.config.app_config import default_config
from src.localization.localization import Localizer

colorama.init(autoreset=True, strip=False)
kernel32 = ctypes.WinDLL('kernel32')
user32 = ctypes.WinDLL('user32')
hWnd = kernel32.GetConsoleWindow()

if __name__ == "__main__":
    print()
    color_print([("Tomato",f""" _  _  __    __    _____  ____    __    _  _  ____     _  _  ___  ____  ____
( \/ )/__\  (  )  (  _  )(  _ \  /__\  ( \( )(_  _)___( \/ )/ __)(_  _)(  _ \\
 \  //(__)\  )(__  )(_)(  )   / /(__)\  )  (   )( (___)\  / \__ \  )(   )   /
  \/(__)(__)(____)(_____)(_)\_)(__)(__)(_)\_) (__)     (__) (___/ (__) (_)\_) """),("White",f"{default_config['version']}\n")])
    color_print([("White", "Original code by colinhartigan.\n\n")])

    try:
        app = Startup()
    except:
        user32.ShowWindow(hWnd, 1)
        kernel32.SetConsoleMode(kernel32.GetStdHandle(-10), (0x4|0x80|0x20|0x2|0x10|0x1|0x40|0x100))
        color_print([("Red bold",Localizer.get_localized_text("prints","errors","error_message"))])
        traceback.print_exc()
        input(Localizer.get_localized_text("prints","errors","exit"))
        os._exit(1)