import os, sys, json

from .config.constants import Constants

class Filepath:

    @staticmethod
    def get_path(relative_path):
        if hasattr(sys, '_MEIPASS'):
            return os.path.join(sys._MEIPASS, relative_path)
        return os.path.join(os.path.abspath("."), relative_path)

    @staticmethod
    def get_appdata_folder():
        return Filepath.get_path(os.path.join(os.getenv('APPDATA'), Constants.PROGRAM_NAME))

    @staticmethod
    def get_rcs_path():
        riot_installs_path = os.path.expandvars("%PROGRAMDATA%\\Riot Games\\RiotClientInstalls.json")
        try:
            with open(riot_installs_path, "r") as file:
                client_installs = json.load(file)
                rcs_path = os.path.abspath(client_installs["rc_default"])
                if not os.access(rcs_path, os.X_OK):
                    raise IOError(f"Your Riot Client Services executable is for some reason not executable! Check the file permissions of {rcs_path}")

                return rcs_path
        except FileNotFoundError:
            raise IOError(f"Could not find Riot Client Services install location at {riot_installs_path}!")