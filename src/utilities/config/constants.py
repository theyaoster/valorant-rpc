class Constants:

    VERSION_NUMBERS = (0, 1, 2, 0)
    VERSION_STR = ".".join([str(num) for num in VERSION_NUMBERS[0:3]])
    VERSION_VSTR = "v" + VERSION_STR
    VERSION_FILENAME = "version.py"
    WHOAMI = "Brian Yao"

    PROGRAM_NAME = "VALORANT-ystr"
    PROGRAM_EXE = PROGRAM_NAME + ".exe"
    PROGRAM_PROC_COUNT = 2 # Number of active processes per instance of this program
    GAME_EXES = ["VALORANT-Win64-Shipping.exe", "RiotClientServices.exe"]
    GAME_CLIENT_UX_EXES = ["RiotClientUx.exe", "RiotClientUxRender.exe"]

    ICON_URI = "https://raw.githubusercontent.com/theyaoster/valorant-ystr/master/favicon.ico"
    ICON_FILENAME = "favicon.ico"

    CONFIG_FILENAME = "config.json"

    LATEST_RELEASE_API_URL = "https://api.github.com/repos/theyaoster/valorant-ystr/releases/latest"
    REPO_URL = "https://github.com/theyaoster/valorant-ystr"