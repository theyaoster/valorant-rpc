from InquirerPy.utils import color_print
import os, ctypes, colorama

from src.startup import Startup
from src.config.constants import Constants
from src.utility_functions import ErrorHandling

colorama.init(autoreset=True)

if __name__ == "__main__":
    print()
    color_print([("Tomato", f""" _  _  __    __    _____  ____    __    _  _  ____     _  _  ___  ____  ____
( \/ )/__\  (  )  (  _  )(  _ \  /__\  ( \( )(_  _)___( \/ )/ __)(_  _)(  _ \\
 \  //(__)\  )(__  )(_)(  )   / /(__)\  )  (   )( (___)\  / \__ \  )(   )   /
  \/(__)(__)(____)(_____)(_)\_)(__)(__)(_)\_) (__)     (__) (___/ (__) (_)\_)   """), ("White", f"{Constants.VERSION_VSTR}\n\n"), ("White", "Original code by colinhartigan.\n")])

    try:
        ctypes.windll.kernel32.SetConsoleTitleW(f"{Constants.PROGRAM_NAME} {Constants.VERSION_VSTR}") # Set window title
        user32 = ctypes.WinDLL('user32')
        kernel32 = ctypes.WinDLL('kernel32')
        window = kernel32.GetConsoleWindow()
        kernel32.SetConsoleMode(kernel32.GetStdHandle(-10), (0x4|0x80|0x20|0x2|0x10|0x1|0x00|0x100)) # Disable inputs to console
        kernel32.SetConsoleMode(kernel32.GetStdHandle(-11), 7) # Allow ANSI sequences

        Startup()
    except Exception:
        ErrorHandling.handle_error()
        os._exit(1)