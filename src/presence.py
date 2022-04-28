from valclient.exceptions import PhaseError, ResponseError
import time, os

from .utility_functions import ContentUtilities, ErrorHandling, Logger, ContentLoader
from .localization.localization import Localizer
from .lib.killable_thread import KillableThread
from .lib.ystr_client import YstrClient

# Implementation of a thread that polls for the player's game presence
class Presence:

    def __init__(self, config):
        self.config = config
        self.client = None
        self.ystr_client = YstrClient(self.config)
        self.content_data = {}
        self.current_status = None

    # Poll game presence
    def main_loop(self):
        sleep_duration = int(Localizer.get_config_value("presence_refresh_interval"))
        while True:
            self.update_if_status_changed()
            time.sleep(sleep_duration)

    # Start the thread to continuously poll game presence
    def start_thread(self):
        try:
            self.content_data = ContentLoader.load_all_content(self.client)
            self.presence_thread = KillableThread(target=self.main_loop, daemon=True)
            self.presence_thread.start()
        except Exception as e:
            Logger.debug(f"Error occured while fetching content or initiating presence thread: {e}")

            ErrorHandling.handle_error()
            self.kill_presence_thread()

    # Only update status if a change is detected - this reduces network usage
    def update_if_status_changed(self, status_override=None):
        last_status = self.current_status
        live_status = status_override
        if status_override is None:
            try:
                presence_data = self.client.fetch_presence()
            except (PhaseError, ResponseError) as game_error:
                # Some valclient-related error
                Logger.debug(f"Ran into valclient error {game_error.__class__.__name__}: {game_error}")
                return
            except Exception as generic_error:
                # Presence unexpectedly stopped
                self.kill_presence_thread(f"Exiting due to error while fetching presence: {generic_error}")

            if presence_data is not None:
                live_status = self.get_status(presence_data)
            else:
                # Presence data is empty...
                self.kill_presence_thread(f"Presence data was blank - assuming game was closed. Exiting.")

        if last_status != live_status and live_status is not None: # If live_status is None, something like a PhaseError occurred
            self.ystr_client.update_status(live_status)
            self.current_status = live_status

    # Get the status of a player
    def get_status(self, presence_data):
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
        elif status_type == "MATCHMADE_GAME_STARTING":
            return self.get_matchmade_status(presence_data, self.content_data)
        else:
            # Unknown status type
            message = f"Unknown status type: {status_type}"
            Logger.debug(message)
            raise ValueError(message)

    # Status string for game startup
    def get_startup_status(self):
        return Localizer.get_localized_text("presences", "startup", "loading")

    # Status string for in menus
    def get_menu_status(self, data, content_data):
        _, mode_name = ContentUtilities.fetch_mode_data(data,content_data)
        if data["partyState"] == "DEFAULT": # In lobby
            return f"{mode_name} - {Localizer.get_localized_text('presences', 'client_states', 'menu')} {ContentUtilities.get_party_status(data)}"
        elif data["partyState"] == "MATCHMAKING": # In queue
            return f"{mode_name} - {Localizer.get_localized_text('presences', 'client_states', 'queue')} {ContentUtilities.get_party_status(data)}"
        elif data["partyState"] == "CUSTOM_GAME_SETUP": # In Custom setup
            data["MapID"] = data["matchMap"]
            _, map_name = ContentUtilities.fetch_map_data(data, content_data)
            return f"{Localizer.get_localized_text('presences', 'client_states', 'custom_setup')} - {map_name} {ContentUtilities.get_party_status(data)}"
        else:
            # Unknown party state
            Logger.debug(f"Unknown party state: {data['partyState']}")
            raise ValueError(f"Unknown party state: {data['partyState']}")

    # Status when match is found but not started
    def get_matchmade_status(self, data, content_data):
        _, mode_name = ContentUtilities.fetch_mode_data(data, content_data)
        return f"{mode_name} - Match Found {ContentUtilities.get_party_status(data)}"

    # Status string for pregame (agent select)
    def get_pregame_status(self, data, content_data):
        _, mode_name = ContentUtilities.fetch_mode_data(data, content_data)
        return f"{mode_name} - {Localizer.get_localized_text('presences','client_states','pregame')} {ContentUtilities.get_party_status(data)}"

    # Status string for in-game (and the range)
    def get_ingame_status(self, data, content_data):
        if data["provisioningFlow"] == "ShootingRange":
            data["MapID"] = "/Game/Maps/Poveglia/Range"
            return f"The Range {ContentUtilities.get_party_status(data)}"
        else:
            _, mode_name = ContentUtilities.fetch_mode_data(data, content_data)
            my_score, other_score = data["partyOwnerMatchScoreAllyTeam"], data["partyOwnerMatchScoreEnemyTeam"]
            return f"{mode_name} - {my_score} to {other_score} {ContentUtilities.get_party_status(data)}"

    # Status string for AFK (Idle)
    def get_afk_status(self, data, content_data):
        _, mode_name = ContentUtilities.fetch_mode_data(data, content_data)
        return f"{mode_name} - {Localizer.get_localized_text('presences', 'client_states', 'away')} {ContentUtilities.get_party_status(data)}"

    # Helper for killing this thread while notifying the user and the web service
    def kill_presence_thread(self, message=""):
        Logger.debug(f"Killing presence thread due to: {message}")

        self.ystr_client.offline()
        os._exit(1)