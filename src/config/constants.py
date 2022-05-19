class Constants:

    # Version data
    VERSION_NUMBERS = (0, 1, 3, 0)
    VERSION_STR = ".".join([str(num) for num in VERSION_NUMBERS[0:3]])
    VERSION_SUFFIX = "b"
    VERSION_VSTR = "v" + VERSION_STR + VERSION_SUFFIX
    VERSION_FILENAME = "version.py"
    WHOAMI = "Brian Yao"

    # Process info
    PROGRAM_NAME = "VALORANT-ystr"
    PROGRAM_EXE = PROGRAM_NAME + ".exe"
    PROGRAM_PROC_COUNT = 2 # Number of active processes per instance of this program
    GAME_EXES = ["VALORANT-Win64-Shipping.exe", "RiotClientServices.exe"]
    GAME_CLIENT_UX_EXES = ["RiotClientUx.exe", "RiotClientUxRender.exe"]

    # Resources
    ICON_URI = "https://raw.githubusercontent.com/theyaoster/valorant-ystr/master/favicon.ico"
    LATEST_RELEASE_API_URL = "https://api.github.com/repos/theyaoster/valorant-ystr/releases/latest"
    REPO_URL = "https://github.com/theyaoster/valorant-ystr"

    # Filenames
    CONFIG_FILENAME = "config.json"
    ICON_FILENAME = "favicon.ico"
    LOG_FILENAME = "debug.log"

    # Field names
    NAME = "name"
    SECRET = "secret"
    ENDPOINT = "endpoint"
    STATUS = "status"
    CONTRACT = "contract_agent"
    IGN = "ign"

    # Values
    LOADING_STATUS = "Loading"
    OFFLINE_STATUS = "Offline"
    UPDATING_STATUS = "Updating"

    # API paths
    LIVE_STATUS_PATH = "live_status"
    CONTRACT_PATH = "contract"
    GAME_DATA_PATH = "game_data"