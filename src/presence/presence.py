from InquirerPy.utils import color_print
from valclient.exceptions import PhaseError
import time, os, ssl

from .presence_utilities import Utilities
from ..utilities.error_handling import handle_error

ssl_context = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
ssl_context.check_hostname = False
ssl_context.verify_mode = ssl.CERT_NONE

from ..content.content_loader import Loader
from ..localization.localization import Localizer
from ..utilities.logging import Logger
from ..utilities.ystr_client import YstrClient

class Presence:

    def __init__(self, config):
        self.config = config
        self.client = None
        self.saved_locale = None
        self.ystr_client = YstrClient(self.config)
        self.content_data = {}
        self.current_status = None

    def main_loop(self):
        while True:
            self.update_if_status_changed()

            if Localizer.locale != self.saved_locale:
                self.saved_locale = Localizer.locale
                self.content_data = Loader.load_all_content(self.client)
            time.sleep(Localizer.get_config_value("presence_refresh_interval"))

    def init_loop(self):
        try:
            self.content_data = Loader.load_all_content(self.client)
            color_print([("LimeGreen bold", Localizer.get_localized_text("prints","presence","presence_running"))])

            self.update_if_status_changed()

            self.main_loop()
        except Exception:
            handle_error()
            self.kill_presence_thread()

    # Only update status if a change is detected - this reduces network usage
    def update_if_status_changed(self, status_override=None):
        last_status = self.current_status
        live_status = status_override
        if status_override is None:
            try:
                presence_data = self.client.fetch_presence()
            except Exception as e:
                # Presence unexpectedly stopped
                self.kill_presence_thread(f"Exiting due to error while fetching presence: {e}")

            if presence_data is not None:
                live_status = self.get_status(presence_data)
            else:
                # Presence data is empty...
                self.kill_presence_thread(f"Presence data was blank - assuming game was closed. Exiting.")
        if last_status != live_status and live_status is not None:
            self.ystr_client.update_status(live_status)
            self.current_status = live_status

    # Get the status of a player
    def get_status(self, presence_data=None):
        status_type = presence_data["sessionLoopState"]
        if presence_data["isIdle"]:
            return self.get_afk_status(presence_data, self.content_data)
        elif status_type == "startup":
            return self.get_startup_status()
        elif status_type == "MENUS":
            return self.get_menu_status(presence_data, self.content_data)
        elif status_type == "PREGAME":
            return self.get_pregame_status(presence_data, self.content_data)
        elif status_type == "INGAME":
            return self.get_ingame_status(presence_data, self.content_data)
        else:
            # Unknown status type
            Logger.debug(f"Unknown status type: {status_type}")

    # Status string for game startup
    def get_startup_status(self):
        return Localizer.get_localized_text("presences", "startup", "loading")

    # Status string for in menus
    def get_menu_status(self, data, content_data):
        _, mode_name = Utilities.fetch_mode_data(data,content_data)
        if data["partyState"] == "DEFAULT":
            # In lobby
            return f"{mode_name} - {Localizer.get_localized_text('presences', 'client_states', 'menu')} {Utilities.get_party_status(data)}"
        elif data["partyState"] == "MATCHMAKING":
            # In queue
            return f"{mode_name} - {Localizer.get_localized_text('presences', 'client_states', 'queue')} {Utilities.get_party_status(data)}"
        elif data["partyState"] == "CUSTOM_GAME_SETUP":
            # In Custom setup
            data["MapID"] = data["matchMap"]
            _, map_name = Utilities.fetch_map_data(data, content_data)
            return f"{Localizer.get_localized_text('presences', 'client_states', 'custom_setup')} - {map_name} {Utilities.get_party_status(data)}"
        else:
            # Unknown party state
            Logger.debug(f"Unknown party state: {data['partyState']}")
            raise ValueError(f"Unknown party state: {data['partyState']}")

    # Status string for pregame (agent select)
    def get_pregame_status(self, data, content_data):
        try:
            _, mode_name = Utilities.fetch_mode_data(data, content_data)
            return f"{mode_name} - {Localizer.get_localized_text('presences','client_states','pregame')} {Utilities.get_party_status(data)}"
        except PhaseError as e:
            Logger.debug(f"Ran into PhaseError (pregame): {e}")
            return None

    # Status string for in-game (and the range)
    def get_ingame_status(self, data, content_data):
        try:
            coregame = self.client.coregame_fetch_player()
            if coregame is not None:
                if data["provisioningFlow"] == "ShootingRange":
                    data["MapID"] = "/Game/Maps/Poveglia/Range"
                    return f"The Range {Utilities.get_party_status(data)}"
                else:
                    _, mode_name = Utilities.fetch_mode_data(data, content_data)
                    my_score, other_score = data["partyOwnerMatchScoreAllyTeam"], data["partyOwnerMatchScoreEnemyTeam"]
                    return f"{mode_name} - {my_score} to {other_score} {Utilities.get_party_status(data)}"
        except PhaseError as e:
            Logger.debug(f"Ran into PhaseError (in-game): {e}")
            return None

    # Status string for AFK (Idle)
    def get_afk_status(self, data, content_data):
        _, mode_name = Utilities.fetch_mode_data(data, content_data)
        return f"{mode_name} - {Localizer.get_localized_text('presences', 'client_states', 'away')} {Utilities.get_party_status(data)}"

    # Helper for killing this thread while notifying the user and the web service
    def kill_presence_thread(self, message=""):
        Logger.debug(f"Killing presence thread due to: {message}")
        self.ystr_client.offline()
        os._exit(1)