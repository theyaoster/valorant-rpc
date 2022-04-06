import requests
from InquirerPy.utils import color_print

from ..localization.localization import Localizer
from .logging import Logger
from .config.constants import Constants

VERSION_CHECKER_TIMEOUT = 3 # seconds

class VersionChecker:

    @staticmethod
    def check():
        try:
            data = requests.get(Constants.LATEST_RELEASE_API_URL, timeout=VERSION_CHECKER_TIMEOUT)
            latest = data.json()["tag_name"]
            if latest != Constants.VERSION_VSTR:
                color_print([("Yellow bold", f"({Constants.VERSION_VSTR} -> {latest}) {Localizer.get_localized_text('prints', 'version_checker', 'update_available')} "), ("Cyan underline", f"{Constants.REPO_URL}/releases/tag/{latest}")])
        except Exception as e:
            color_print([("Yellow bold", Localizer.get_localized_text("prints", "version_checker", "checker_error"))])
            Logger.debug(f"Error occurred while checking if an update is available: {e}")