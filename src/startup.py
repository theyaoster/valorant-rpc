from InquirerPy.utils import color_print
from colorama import Fore, Style, Cursor, ansi
import subprocess, time, cursor, valclient, ctypes, os, sys, requests

from .utilities.error_handling import handle_error
from .utilities.killable_thread import KillableThread
from .utilities.config.app_config import Config
from .utilities.processes import Processes
from .utilities.filepath import Filepath
from .utilities.systray import Systray
from .utilities.version_checker import VersionChecker
from .utilities.logging import Logger

from .localization.localization import Localizer

from .presence.presence import Presence

GAME_CMD_TIMEOUT = 5 # seconds

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

            VersionChecker.check() # If an update's available, print a message

            # Attempt to initialize http client
            try:
                self.presence = Presence(self.config)
            except Exception as e:
                handle_error(e)
                os._exit(1)

            self.start_game() # Launch the game and wait for its processes to exist

            # Autodetect game region if it's not specified in the config (game must be running for this to work)
            if Localizer.autodetect_region(self.config):
                Config.modify_config(self.config)

            Logger.debug("About to initialize regionalized valclient...")

            # Initialize client for VALORANT's client-api
            self.client = valclient.Client(region=Localizer.get_config_value("region", 0))
            self.client.activate()
            self.presence.client = self.client

            Logger.debug("About to dispatch systray thread...")

            # Initialize the systray element
            self.systray = Systray(self.client, self.config)
            self.systray_thread = KillableThread(target=self.systray.run)
            self.systray_thread.start()

            self.wait_for_presence() # Poll game presence until the presence data isn't empty

            Logger.debug("About to dispatch presence thread...")

            self.presence.start_thread() # Initialize the thread that will poll the player status

            color_print([("LimeGreen", f"{Localizer.get_localized_text('prints', 'startup', 'startup_successful')}\n")])
            time.sleep(5)
            ctypes.WinDLL('user32').ShowWindow(ctypes.WinDLL('kernel32').GetConsoleWindow(), 0) # Hide the window

            Logger.debug("Program's up and running. Waiting for systray thread to terminate...")

            # Wait until systray thread terminates
            self.systray_thread.join()
            self.presence.presence_thread.stop()

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

                    self.die()

                time.sleep(1) # Wait 1 second
        except requests.exceptions.ConnectionError:
            Logger.debug("Failed to fetch presence from the client due to refused connection - exiting.")

            self.die()

        clear_last_line()

    # Start VALORANT - this will return when the game process is detected
    def start_game(self):
        # Do nothing if game is already running
        Logger.debug("Checking if game is already running...")

        if Processes.are_processes_running():
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
        while not Processes.are_processes_running():
            clear_last_line()

            color_print([("Cyan", "["), ("White", str(launch_timer)), ("Cyan", f"] {Localizer.get_localized_text('prints', 'startup', 'waiting_for_valorant')}")])
            launch_timer += 1

            # Check if game is updating
            if launch_timer == update_time:
                Logger.debug("Checking if the game is updating...")

                if Processes.is_updating():
                    Logger.debug("Game is updating. Waiting for user to execute manual step...")

                    clear_last_line()
                    self.presence.update_if_status_changed("Updating") # Dedicated updating status
                    input(f"{Style.BRIGHT}{Fore.YELLOW}I think your game is updating. Press {Fore.MAGENTA}Enter{Fore.YELLOW} when you're finished and have launched the game...")
                    launch_timer = 0
                else:
                    Logger.debug("Verified that the game is not updating. Proceeding to wait for game launch...")

            # Check if timeout is exceeded
            if launch_timer >= launch_timeout:
                Logger.debug("Timed out waiting for game!")

                self.die()

            time.sleep(1) # Wait 1 second

        clear_last_line()
        clear_last_line()

    # Config initialization business
    def load_and_localize_config(self):
        self.config = Config.fetch_config()
        Localizer.prompt_locale(self.config)
        Localizer.set_locale(self.config)
        self.config = Config.localize_config(self.config)
        Config.modify_config(self.config)
        Localizer.config = self.config

    # Helper to handle program exit in the case of unexpected failures
    def die(self):
        if self.systray is not None:
            self.systray.exit()
        os._exit(1)