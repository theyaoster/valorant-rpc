import json, os
from colorama import Fore, Style
from valclient.client import Client

from ..filepath import Filepath

from ...localization.locales import Locales
from ...localization.localization import Localizer
from ..logging import Logger

PLACEHOLDER_VALUE = "THIS IS A PLACEHOLDER"

default_config = {
    "version": "v0.1.2",
    "region": ["",Client.fetch_regions()],
    "client_id": 811469787657928704,
    "presence_refresh_interval": 3,
    "locale": ["",[locale for locale,data in Locales.items() if data != {}]],
    "presences": {
        "menu": {
            "show_rank_in_comp_lobby": True,
        },
        "modes": {
            "all": {
                "small_image": ["agent",["rank","agent","map"]],
                "large_image": ["map",["rank","agent","map"]],
            },
            "range": {
                "show_rank_in_range": False,
            }
        }
    },
    "startup": {
        "game_launch_timeout": 60,
        "check_if_updating_time": 15,
        "presence_timeout": 60,
        "show_github_link": False,
        "auto_launch_skincli": False,
    },
    "endpoint": PLACEHOLDER_VALUE, # Adding these here so they aren't autodeleted upon launch
    "name": PLACEHOLDER_VALUE,
    "secret": PLACEHOLDER_VALUE
}

class Config:

    @staticmethod
    def fetch_config():
        config_path = Filepath.get_path(os.path.join(Filepath.get_appdata_folder(), "config.json"))

        # Handle first-time startup when config file doesn't exist
        if not os.path.isfile(config_path):
            os.makedirs(Filepath.get_path(os.path.join(Filepath.get_appdata_folder())), exist_ok=True)
            Config.modify_config(default_config) # write default config
            print(f"Generated default config at {Fore.BLUE}{config_path}")
            print(f"{Style.BRIGHT}{Fore.YELLOW}Modify the 3 placeholder values in the config file before you proceed.\n")

            os.startfile(config_path) # open config file in default editor

            typed = None
            while typed != "done":
                typed = input(f"Type \"{Style.BRIGHT}{Fore.MAGENTA}done{Style.RESET_ALL}\" once you've updated the config values... ")

        try:
            with open(Filepath.get_path(os.path.join(Filepath.get_appdata_folder(), "config.json"))) as f:
                config = json.load(f)
                return config
        except Exception as e:
            Logger.debug(f"Something went wrong while fetching config: {e}")

    @staticmethod
    def modify_config(new_config):
        with open(Filepath.get_path(os.path.join(Filepath.get_appdata_folder(), "config.json")), "w") as f:
            json.dump(new_config, f)

        return Config.fetch_config()

    @staticmethod
    def check_config():
        # ???????
        # my brain hurts
        # i bet theres a way better way to write this but im just braindead
        config = Config.fetch_config()
        unlocalized_config = Config.localize_config(config,True)

        def check_for_new_vars(blank,current):
            for key,value in blank.items():
                if not key in current.keys():
                    current[key] = value
                if type(value) != type(current[key]):
                    # if type of option is changed
                    current[key] = value
                if key == "version":
                    # version can't be changed by the user lmao
                    current[key] = value
                if key == "region":
                    current[key][1] = Client.fetch_regions() # update regions jic ya know
                if isinstance(value,list):
                    current[key][0] = current[key][0]
                    current[key][1] = blank[key][1]
                    if not current[key][0] in blank[key][1]:
                        current[key][0] = blank[key][0]
                if isinstance(value,dict):
                    check_for_new_vars(value,current[key])
            return current

        def remove_unused_vars(blank,current):
            def check(bl,cur):
                for key,value in list(cur.items()):
                    if not key in bl.keys():
                        del cur[key]
                    if isinstance(value,dict) and key in list(cur.keys()):
                        check(bl[key],value)

            check(blank,current)
            return current

        unlocalized_config = check_for_new_vars(default_config,unlocalized_config)
        unlocalized_config = remove_unused_vars(default_config,unlocalized_config)
        config = Config.localize_config(unlocalized_config)
        Config.modify_config(config)
        return config


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

    @staticmethod
    def create_default_config():
        if not os.path.exists(Filepath.get_appdata_folder()):
            os.mkdir(Filepath.get_appdata_folder())
        with open(Filepath.get_path(os.path.join(Filepath.get_appdata_folder(), "config.json")), "w") as f:
            json.dump(default_config, f)
        return Config.fetch_config()
