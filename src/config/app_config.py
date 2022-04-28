import json, os, copy, getpass, cursor
from colorama import Fore, Style
from valclient.client import Client

from ..utility_functions import Filepath, Logger, ErrorHandling

from ..localization.locales import Locales
from ..localization.localization import Localizer
from .constants import Constants

CONFIG_FILEPATH = Filepath.get_path(os.path.join(Filepath.get_appdata_folder(), Constants.CONFIG_FILENAME))

PLACEHOLDER_VALUE = "THIS IS A PLACEHOLDER"

default_config = {
    "region": ["", Client.fetch_regions()],
    "presence_refresh_interval": 2,
    "locale": ["", [locale for locale, data in Locales.items() if data != {}]],
    "startup": {
        "game_launch_timeout": 60,
        "presence_timeout": 60,
        "check_if_updating_time": 30,
        "check_if_updating_freq": 10,
    },
    "endpoint": PLACEHOLDER_VALUE, # Adding these here so they aren't autodeleted upon launch
    "name": PLACEHOLDER_VALUE,
    "secret": PLACEHOLDER_VALUE
}

class ApplicationConfig:

    @staticmethod
    def fetch_config():
        # Handle first-time startup when config file doesn't exist
        if not os.path.isfile(CONFIG_FILEPATH):
            os.makedirs(Filepath.get_path(os.path.join(Filepath.get_appdata_folder())), exist_ok=True)
            print(f"{Fore.YELLOW}As this is the first time you're launching this, you'll need to enter the following required configs.\n")

            # Prompt user for required configs
            cursor.show()
            initial_config = copy.deepcopy(default_config)
            initial_config["name"] = input(f"{Style.BRIGHT}{Fore.WHITE}Enter your registered name: ").strip()
            initial_config["secret"] = getpass.getpass(f"{Style.BRIGHT}{Fore.WHITE}Enter your registered secret: ").strip()
            initial_config["endpoint"] = input(f"{Style.BRIGHT}{Fore.WHITE}Enter the web endpoint you wish to reach: ").strip()
            print()
            cursor.hide()

            # Save inputs to disk
            ApplicationConfig.modify_config(initial_config)
            return initial_config

        try:
            with open(CONFIG_FILEPATH) as f:
                config = json.load(f)
                return config
        except Exception as e:
            Logger.debug(f"Something went wrong while fetching config: {e}")
            ErrorHandling.handle_error()

    @staticmethod
    def modify_config(new_config):
        with open(CONFIG_FILEPATH, "w") as f:
            json.dump(new_config, f)

        return ApplicationConfig.fetch_config()

    @staticmethod
    def localize_config(config,unlocalize=False):
        def check(blank,current):
            for key,value in list(blank.items() if not unlocalize else current.items()):
                new_key = Localizer.get_config_key(key) if not unlocalize else Localizer.unlocalize_key(key)
                if new_key != key:
                    if unlocalize:
                        current[new_key] = current[key]
                        del current[key]
                    else:
                        current[new_key] = current[key]
                        del current[key]

                if isinstance(value,list):
                    if not unlocalize:
                        new_options = [Localizer.get_config_key(x) for x in value[1]]
                        current[new_key][0] = Localizer.get_config_key(current[new_key][0])
                        current[new_key][1] = new_options

                    else:
                        new_options = [Localizer.unlocalize_key(x) for x in value[1]]
                        unlocalized = Localizer.unlocalize_key(current[new_key][0])
                        value[0] = unlocalized
                        value[1] = new_options

                if isinstance(value,dict):
                    check(value,current[new_key])

        check(default_config,config)
        return config
