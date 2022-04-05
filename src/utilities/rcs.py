import os, json
from ..utilities.logging import Logger

class RiotClientServices:

    @staticmethod
    def get_rcs_path():
        Logger.debug("Finding Riot Client Services location...")

        riot_installs_path = os.path.expandvars("%PROGRAMDATA%\\Riot Games\\RiotClientInstalls.json")
        try:
            with open(riot_installs_path, "r") as file:
                client_installs = json.load(file)
                rcs_path = os.path.abspath(client_installs["rc_default"])
                if not os.access(rcs_path, os.X_OK):
                    return None

                Logger.debug(f"Found Riot Client Services at {rcs_path}")
                return rcs_path
        except FileNotFoundError:
            raise IOError(f"Could not find Riot Client Services install location at {riot_installs_path}!")
