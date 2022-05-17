from InquirerPy.utils import color_print
from colorama import Fore, Style, Cursor, ansi
import subprocess, time, cursor, valclient, ctypes, os, sys, requests

from .localization.localization import Localizer
from .utility_functions import ContentLoader, Filepath, Processes, Logger, ErrorHandling, VersionChecker
from .lib.killable_thread import KillableThread
from .config.app_config import ApplicationConfig
from .config.constants import Constants
from .daemons.systray import Systray
from .daemons.live_status import LiveStatus
from .daemons.contract_manager import ContractManager

# Helper to clear out the second-to-last line of stdout
def clear_last_line():
    sys.stdout.write(f"{Cursor.UP()}\r{ansi.clear_line()}")

class Startup:

    def __init__(self):
        if not Processes.is_program_already_running():
            Logger.create_logger()
            self.load_and_localize_config()
            self.systray = None # Just so this attribute exists
            cursor.hide()

            VersionChecker.check_version() # If an update's available, print a message

            # Attempt to initialize http client
            try:
                Logger.debug("Creating presence object...")

                self.status_daemon = LiveStatus(self.config)
            except Exception as e:
                Logger.debug(f"Error creating presence: {e}")

                ErrorHandling.handle_error()
                os._exit(1)

            self.start_game() # Launch the game and wait for its processes to exist

            # Autodetect game region if it's not specified in the config (game must be running for this to work)
            self.autodetect_region(self.config)

            Logger.debug("About to initialize regionalized valclient...")

            # Initialize client for VALORANT's client-api
            self.client = valclient.Client(region=Localizer.get_config_value("region", 0))
            self.client.activate()
            self.status_daemon.client = self.client

            Logger.debug("Updating player data (this happens only once per launch)...")
            player_data = self.client.rnet_fetch_active_alias()
            self.status_daemon.ystr_client.update_game_data(f"{player_data['game_name']}#{player_data['tag_line']}")

            Logger.debug("About to initialize contract manager...")

            # Initialize contract manager
            self.contract_manager = ContractManager(self.client, self.config)
            self.contract_manager.start_sync_thread()
            self.contract_manager.start_poll_thread()

            Logger.debug("About to dispatch systray thread...")

            # Initialize the systray element
            self.systray = Systray(self.client, self.config)
            self.systray_thread = KillableThread(target=self.systray.run)
            self.systray_thread.start()

            self.wait_for_presence() # Poll game presence until the presence data isn't empty

            Logger.debug("About to dispatch presence thread...")

            self.status_daemon.start_thread() # Initialize the thread that will poll the player status

            color_print([("LimeGreen", f"{Localizer.get_localized_text('prints', 'startup', 'startup_successful')}\n")])
            time.sleep(5)
            ctypes.WinDLL('user32').ShowWindow(ctypes.WinDLL('kernel32').GetConsoleWindow(), 0) # Hide the window

            Logger.debug("Program's up and running. Waiting for systray thread to terminate...")

            # Wait until systray thread terminates
            self.systray_thread.join()
            self.status_daemon.presence_thread.stop()
            self.contract_manager.sync_thread.stop()
            self.contract_manager.poll_thread.stop()
        else:
            Logger.debug("Program is already running - erroring out.")

            raise Exception("Another instance of this program is already running.")

    # Fetch player presence until it's not empty
    def wait_for_presence(self):
        Logger.debug("Waiting for game presence...")
        print()

        presence_timeout = Localizer.get_config_value("startup", "presence_timeout")
        presence_timer = 0
        try:
            while self.client.fetch_presence() is None:
                clear_last_line()
                color_print([("Cyan", "["), ("White", str(presence_timer)), ("Cyan", f"] {Localizer.get_localized_text('prints','startup','waiting_for_presence')}")])

                presence_timer += 1
                if presence_timer >= presence_timeout:
                    Logger.debug("Timed out waiting for presence!")

                    self.handle_timeout("game presence")

                time.sleep(1) # Wait 1 second
        except requests.exceptions.ConnectionError:
            Logger.debug("Failed to fetch presence from the client due to refused connection - exiting.")

            self.die()

        clear_last_line()

    # Start VALORANT - this will return when the game process is detected
    def start_game(self):
        # Do nothing if game is already running
        if Processes.is_game_running():
            Logger.debug("Game is already running.")

            return

        rcs_path = Filepath.get_rcs_path()
        Logger.debug(f"Found RCS at: {rcs_path}")

        color_print([("Red", Localizer.get_localized_text("prints", "startup", "starting_valorant"))])

        Logger.debug("Game is not already running, launching game...")

        # Attempt to launch the game
        subprocess.Popen([rcs_path, "--launch-product=valorant", "--launch-patchline=live"])

        # Now wait for the game process to exist...
        print()
        launch_timer = 0
        launch_timeout = Localizer.get_config_value("startup", "game_launch_timeout")
        update_time = Localizer.get_config_value("startup", "check_if_updating_time")
        while not Processes.is_game_running():
            clear_last_line()

            color_print([("Cyan", "["), ("White", str(launch_timer)), ("Cyan", f"] {Localizer.get_localized_text('prints', 'startup', 'waiting_for_valorant')}")])
            launch_timer += 1

            # Check if game is updating
            if launch_timer == update_time:
                Logger.debug("Checking if the game is updating...")
                Logger.debug(f"Process list: {Processes.running_processes()}")

                if Processes.is_updating():
                    Logger.debug("Game is updating. Waiting for user to execute manual step...")

                    clear_last_line()
                    print()

                    self.status_daemon.update_if_status_changed(Constants.UPDATING_STATUS)
                    print(f"{Style.BRIGHT}{Fore.YELLOW}I think your game is updating. Waiting until game is launched...")
                    update_wait_time = Localizer.get_config_value("startup", "check_if_updating_freq")
                    while not Processes.is_game_running():
                        time.sleep(update_wait_time)

                    print("Game detected!")
                    launch_timer = 0
                else:
                    Logger.debug("Verified that the game is not updating. Proceeding to wait for game launch...")

            # Check if timeout is exceeded
            if launch_timer >= launch_timeout:
                Logger.debug("Timed out waiting for game!")

                self.handle_timeout("VALORANT to launch")

            time.sleep(1) # Wait 1 second

        clear_last_line()
        clear_last_line()

    # Config initialization business
    def load_and_localize_config(self):
        self.config = ApplicationConfig.fetch_config()
        Localizer.prompt_locale(self.config)
        Localizer.set_locale(self.config)

        Logger.debug("Localizing config...")

        self.config = ApplicationConfig.localize_config(self.config)
        ApplicationConfig.modify_config(self.config)
        Localizer.config = self.config

    def autodetect_region(self, config):
        # If the region is not specified in the config, try to autodetect it (this happens on first launch)
        if Localizer.get_config_value("region", 0) == "":
            color_print([("Yellow", Localizer.get_localized_text("prints", "startup", "autodetect_region"))])

            Logger.debug("About to initialize NA valclient for autodetecting region...")

            # Default to NA for now
            client = valclient.Client()
            client.activate()

            Logger.debug("Client initialized. Now searching active game sessions for VALORANT...")

            # Find the valorant game session and fetch its region
            sessions = client.riotclient_session_fetch_sessions()
            val_session = next(session for _, session in sessions.items() if session["productId"] == "valorant")
            region = next(arg.split("=", 2)[1] for arg in val_session["launchConfiguration"]["arguments"] if "-ares-deployment" in arg) # The value of the ares-deployment arg is the region

            Logger.debug(f"Found region '{region}' from session {val_session}")

            # Update the passed config to specify the detected region
            config[Localizer.get_config_key("region")][0] = region
            color_print([("LimeGreen", f"{Localizer.get_localized_text('prints', 'startup', 'autodetected_region')} {Localizer.get_config_value('region', 0)}\n")])

            ApplicationConfig.modify_config(config)

    # Helper to handle program exit in the case of unexpected failures
    def die(self):
        if self.systray is not None:
            self.systray.exit()
        os._exit(1)

    # Handling timeout events
    def handle_timeout(self, cause):
        color_print([("Red bold", f"Timed out while waiting for {cause}!\n")])
        input(Localizer.get_localized_text("prints", "errors", "exit"))
        self.die()