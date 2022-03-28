from InquirerPy.utils import color_print
import os, colorama

from src.startup import Startup
from src.utilities.config.app_config import default_config
from src.utilities.error_handling import handle_error

colorama.init(autoreset=True, strip=False)

if __name__ == "__main__":
    print()
    color_print([("Tomato", f""" _  _  __    __    _____  ____    __    _  _  ____     _  _  ___  ____  ____
( \/ )/__\  (  )  (  _  )(  _ \  /__\  ( \( )(_  _)___( \/ )/ __)(_  _)(  _ \\
 \  //(__)\  )(__  )(_)(  )   / /(__)\  )  (   )( (___)\  / \__ \  )(   )   /
  \/(__)(__)(____)(_____)(_)\_)(__)(__)(_)\_) (__)     (__) (___/ (__) (_)\_)   """),("White", f"{default_config['version']}\n\n"), ("White", "Original code by colinhartigan.\n\n")])

    try:
        Startup()
    except:
        handle_error()
        os._exit(1)