import requests, psutil, os, sys, json, ctypes, traceback, logging
from InquirerPy.utils import color_print
from requests.adapters import HTTPAdapter, Retry

from .localization.localization import Localizer
from .config.constants import Constants

# Get handle for console window
kernel32 = ctypes.WinDLL('kernel32')
user32 = ctypes.WinDLL('user32')
hWnd = kernel32.GetConsoleWindow()

# Erro handling
class ErrorHandling:

    @staticmethod
    def handle_error(error=None):
        user32.ShowWindow(hWnd, 1)
        kernel32.SetConsoleMode(kernel32.GetStdHandle(-10), (0x4|0x80|0x20|0x2|0x10|0x1|0x40|0x100))
        color_print([("Red bold", Localizer.get_localized_text("prints", "errors", "error_message"))])
        print()
        if error is None:
            traceback.print_exc()
        else:
            color_print([("Red bold", str(error))])
        print()
        input(Localizer.get_localized_text("prints", "errors", "exit"))

# Utilities for active process management and detection
class Processes:

    # Helper to get list of running processes
    @staticmethod
    def running_processes():
        processes = []
        for proc in psutil.process_iter():
            try:
                processes.append(proc.name())
            except psutil.NoSuchProcess as e:
                Logger.debug(f"Failed to find running process: {e}")
                continue

        return processes

    @staticmethod
    def __are_processes_running(processes=None):
        return set(processes).issubset(Processes.running_processes())

    @staticmethod
    def is_program_already_running():
        return Processes.running_processes().count(Constants.PROGRAM_EXE) > Constants.PROGRAM_PROC_COUNT

    @staticmethod
    def is_game_running():
        return Processes.__are_processes_running(Constants.GAME_EXES)

    @staticmethod
    def is_updating():
        return Processes.__are_processes_running(Constants.GAME_CLIENT_UX_EXES)

# Filepath-related utilities
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

# Helpers for processing raw valclient data
class ContentUtilities:

    @staticmethod
    def build_party_state(data):
        party_state = Localizer.get_localized_text("presences","party_states","solo")
        if data["partySize"] > 1:
            party_state = Localizer.get_localized_text("presences","party_states","in_party")
        elif data["partyAccessibility"] == "OPEN":
            party_state = Localizer.get_localized_text("presences","party_states","open")

        party_size = [data["partySize"],data["maxPartySize"]] if data["partySize"] > 1 else [1, 1]
        if party_size is not None:
            if party_size[0] == 0:
                party_size[0] = 1
            if party_size[1] < 1:
                party_size[1] = 1
        return party_state, party_size

    @staticmethod
    def fetch_map_data(coregame_data,content_data):
        for gmap in content_data["maps"]:
            if gmap["path"] == coregame_data["MapID"]:
                return gmap["display_name"], gmap["display_name_localized"]
        return "", ""

    @staticmethod
    def fetch_mode_data(data, content_data):
        image = f"mode_{data['queueId'] if data['queueId'] in content_data['modes_with_icons'] else 'discovery'}"
        mode_name = content_data['queue_aliases'][data['queueId']] if data["queueId"] in content_data["queue_aliases"].keys() else "Custom"

        # For some reason, Custom games have a queueId of onefa, same as Replication...
        if "Custom" in data['provisioningFlow'] and "Custom" not in mode_name:
            mode_name = "Custom"
            data["queueId"] = "custom"

        mode_name = ContentUtilities.localize_content_name(mode_name, "presences", "modes", data["queueId"])
        return image,mode_name

    @staticmethod
    def localize_content_name(default,*keys):
        localized = Localizer.get_localized_text(*keys)
        if localized is not None:
            return localized
        return default

    @staticmethod
    def get_party_status(data):
        size = ContentUtilities.build_party_state(data)[1]
        if (size[0] == 1):
            return "(solo)"
        else:
            return f"(in a {size[0]}-stack)"

class ContentCache:

    def __init__(self):
        self.agents = None
        self.contracts = None
        self.completed_contracts = None

# Utility for loading game content details (this should only be used once per program instance)
class ContentLoader:

    CONTENT_CACHE = ContentCache()
    CONTENT_LOAD_TIMEOUT = 5 # Seconds
    RETRY_STRATEGY = Retry(total=5, backoff_factor=1) # 5 max retries
    SESSION = requests.Session()
    SESSION.mount("https://", HTTPAdapter(max_retries=RETRY_STRATEGY))

    @staticmethod
    def __fetch(endpoint="/", language="all"):
        data = ContentLoader.SESSION.get(f"https://valorant-api.com/v1{endpoint}?language={language}", timeout=ContentLoader.CONTENT_LOAD_TIMEOUT)
        return data.json()

    @staticmethod
    def cache_contracts():
        raw_contract_data = ContentLoader.__fetch("/contracts", "en-US")
        filtered_data = {}
        for contract in raw_contract_data["data"]:
            filtered_data[contract["displayName"].lower().split()[0]] = contract["uuid"]
        ContentLoader.CONTENT_CACHE.contracts = filtered_data

    @staticmethod
    def get_contract(agent):
        if ContentLoader.CONTENT_CACHE.contracts is None:
            ContentLoader.cache_contracts()

        if agent not in ContentLoader.CONTENT_CACHE.contracts:
            raise ValueError(f"Unknown agent {agent}! Could not find their contract.")

        return ContentLoader.CONTENT_CACHE.contracts[agent]

    @staticmethod
    def get_agents():
        if ContentLoader.CONTENT_CACHE.agents is None:
            raw_agent_data = ContentLoader.SESSION.get(f"https://valorant-api.com/v1/agents?language=en-US&isPlayableCharacter=true", timeout=ContentLoader.CONTENT_LOAD_TIMEOUT).json()
            agent_names = [agent["displayName"].lower() for agent in raw_agent_data["data"]]
            ContentLoader.CONTENT_CACHE.agents = agent_names

        return ContentLoader.CONTENT_CACHE.agents

    @staticmethod
    def load_all_content(client):
        Logger.debug("Calling VALORANT API to load game content in memory...")

        content_data = {
            "agents": [],
            "maps": [],
            "modes": [],
            "comp_tiers": [],
            "season": {},
            "queue_aliases": { #i'm so sad these have to be hardcoded but oh well :(
                "newmap": "New Map",
                "competitive": "Competitive",
                "unrated": "Unrated",
                "spikerush": "Spike Rush",
                "deathmatch": "Deathmatch",
                "ggteam": "Escalation",
                "onefa": "Replication",
                "custom": "Custom",
                "snowball": "Snowball Fight",
                "": "Custom",
            },
            "team_aliases": {
                "TeamOne": "Defender",
                "TeamTwo": "Attacker",
                "TeamSpectate": "Observer",
                "TeamOneCoaches": "Defender Coach",
                "TeamTwoCoaches": "Attacker Coach",
            },
            "team_image_aliases": {
                "TeamOne": "team_defender",
                "TeamTwo": "team_attacker",
                "Red": "team_defender",
                "Blue": "team_attacker",
            },
            "modes_with_icons": ["ggteam","onefa","snowball","spikerush","unrated","deathmatch"]
        }
        all_content = client.fetch_content()
        agents = ContentLoader.__fetch("/agents")["data"]
        maps = ContentLoader.__fetch("/maps")["data"]
        modes = ContentLoader.__fetch("/gamemodes")["data"]
        comp_tiers = ContentLoader.__fetch("/competitivetiers")["data"][-1]["tiers"]

        for season in all_content["Seasons"]:
            if season["IsActive"] and season["Type"] == "act":
                content_data["season"] = {
                    "competitive_uuid": season["ID"],
                    "season_uuid": season["ID"],
                    "display_name": season["Name"]
                }

        for agent in agents:
            content_data["agents"].append({
                "uuid": agent["uuid"],
                "display_name": agent["displayName"]["en-US"],
                "display_name_localized": agent["displayName"][Localizer.locale],
                "internal_name": agent["developerName"]
            })

        for game_map in maps:
            content_data["maps"].append({
                "uuid": game_map["uuid"],
                "display_name": game_map["displayName"]["en-US"],
                "display_name_localized": game_map["displayName"][Localizer.locale],
                "path": game_map["mapUrl"],
                "internal_name": game_map["mapUrl"].split("/")[-1]
            })

        for mode in modes:
            content_data["modes"].append({
                "uuid": mode["uuid"],
                "display_name": mode["displayName"]["en-US"],
                "display_name_localized": mode["displayName"][Localizer.locale],
            })

        for tier in comp_tiers:
            content_data["comp_tiers"].append({
                "display_name": tier["tierName"]["en-US"],
                "display_name_localized": tier["tierName"][Localizer.locale],
                "id": tier["tier"],
            })

        Logger.debug("Done loading game content.")

        return content_data

# Version checking of this program
class VersionChecker:

    VERSION_CHECKER_TIMEOUT = 3 # seconds

    @staticmethod
    def check_version():
        try:
            data = requests.get(Constants.LATEST_RELEASE_API_URL, timeout=VersionChecker.VERSION_CHECKER_TIMEOUT)
            latest = data.json()["tag_name"]
            if latest != Constants.VERSION_VSTR:
                color_print([("Yellow bold", f"({Constants.VERSION_VSTR} -> {latest}) {Localizer.get_localized_text('prints', 'version_checker', 'update_available')} "), ("Cyan underline", f"{Constants.REPO_URL}/releases/tag/{latest}")])
        except Exception as e:
            color_print([("Yellow bold", Localizer.get_localized_text("prints", "version_checker", "checker_error"))])
            Logger.debug(f"Error occurred while checking if an update is available: {e}")

# Debug-level logger
class Logger:

    @staticmethod
    def create_logger():
        # To not get swamped with (mostly) irrelevant log messages...
        logging.getLogger("urllib3").setLevel(logging.WARNING)
        logging.getLogger("PIL.Image").setLevel(logging.WARNING)

        # Create logger
        os.makedirs(Filepath.get_path(Filepath.get_appdata_folder()), exist_ok=True)
        logging.basicConfig(filename=Filepath.get_path(os.path.join(Filepath.get_appdata_folder(), Constants.LOG_FILENAME)),
                            filemode='w+',
                            format='[%(asctime)s.%(msecs)d %(name)s %(levelname)s]: %(message)s',
                            datefmt='%H:%M:%S',
                            level=logging.DEBUG)

    @staticmethod
    def debug(data):
        logger = logging.getLogger(Constants.PROGRAM_NAME)
        logger.debug(data)