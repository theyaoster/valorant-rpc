import json, os, copy, getpass, cursor
from colorama import Fore, Style
from valclient.client import Client

from ..utility_functions import Filepath, Logger, ErrorHandling

from ..localization.locales import Locales
from ..localization.localization import Localizer
from .constants import Constants

CONFIG_FILEPATH = Filepath.get_path(os.path.join(Filepath.get_appdata_folder(), Constants.CONFIG_FILENAME))

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
    "publish_state_to_web": False, # Set to True to enable publishing state to web endpoint
    Constants.ENDPOINTS: { # Hash of endpoints and where to include the status in the json payload (must include $STATUS as a placeholder)
        # www.myurl.com": { "some_field": "$STATUS" }
    },
    "publish_state_to_file": False, # Set to True to enable publishing state to file
    Constants.STATE_FILES: { # Hash of data fields and the text files they should be written to (this will truncate, not append!)
        # "sessionLoopState": [ "state.txt" ]
    }
}

class ApplicationConfig:

    @staticmethod
    def fetch_config():
        # Handle first-time startup when config file doesn't exist
        if not os.path.isfile(CONFIG_FILEPATH):
            os.makedirs(Filepath.get_path(os.path.join(Filepath.get_appdata_folder())), exist_ok=True)
            print(f"{Fore.YELLOW}Please enter the required configs.\n")

            # Prompt user for required configs
            cursor.show()
            initial_config = copy.deepcopy(default_config)

            publish_web = input(f"{Style.BRIGHT}{Fore.WHITE}Publish your game status? (y/N) ").strip()
            if publish_web.lower() in ["y", "yes"]:
                name = input(f"{Style.BRIGHT}{Fore.WHITE}Enter your registered name: ").strip()
                secret = getpass.getpass(f"{Style.BRIGHT}{Fore.WHITE}Enter your registered secret: ").strip()
                endpoint = input(f"{Style.BRIGHT}{Fore.WHITE}Enter the web URL you wish to reach: ").strip()
                if not endpoint.startswith("https://"):
                    endpoint = "https://" + endpoint

                initial_config["publish_state_to_web"] = True
                initial_config[Constants.ENDPOINTS] = { endpoint: { Constants.STATUS: Constants.STATUS_PLACEHOLDER, Constants.NAME: name, Constants.SECRET: secret } }

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

        # Initialize keys to default if they don't exist in the current config
        for key in default_config:
            if key not in config:
                config[key] = default_config[key]

        return config
