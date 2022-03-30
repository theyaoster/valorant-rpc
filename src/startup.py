from InquirerPy.utils import color_print
from colorama import Fore, Style, Cursor, ansi
import psutil, time, cursor, valclient, ctypes, os, sys

from .utilities.killable_thread import KillableThread
from .utilities.config.app_config import Config
from .utilities.processes import Processes
from .utilities.rcs import RiotClientServices
from .utilities.systray import Systray
from .utilities.version_checker import Checker
from .utilities.logging import Logger
from .utilities.program_data import ProgramData

from .localization.localization import Localizer

from .presence.presence import Presence

user32 = ctypes.WinDLL('user32')
kernel32 = ctypes.WinDLL('kernel32')
window = kernel32.GetConsoleWindow()

# Helper to clear out the current line of stdout
def clear_current_line():
    sys.stdout.write(f"{Cursor.UP()}\r{ansi.clear_line()}")

class Startup:

    def __init__(self):
        if not Processes.is_program_already_running():
            self.config = Config.fetch_config()
            if self.config["locale"][0] == "":
                config = Localizer.prompt_locale(self.config)
                Config.modify_config(config)

            cursor.hide()
            Logger.create_logger()
            ProgramData.update_file_location()
            ProgramData.fetch_installs()
            Localizer.set_locale(self.config)
            self.config = Config.check_config()
            Localizer.config = self.config

            # If an update's available, print a message
            Checker.check_version(self.config)

            # Initialize http client
            self.presence = Presence(self.config)

            # Launch the game
            self.start_game()

            # Autodetect game region if it's not specified in the config (game must be running for this to work)
            Localizer.autodetect_region(self.config)
            Config.modify_config(self.config)

            # Initialize client for VALORANT's client-api
            self.client = valclient.Client(region=Localizer.get_config_value("region", 0))
            self.client.activate()
            self.presence.client = self.client

            # Initialize the systray element
            self.systray = Systray(self.client, self.config)
            self.systray_thread = KillableThread(target=self.systray.run)
            self.systray_thread.start()

            # Initialize the thread that will poll the player status
            self.wait_for_presence()
            self.presence.start_thread()

            color_print([("LimeGreen", f"{Localizer.get_localized_text('prints', 'startup', 'startup_successful')}\n")])
            time.sleep(5)
            user32.ShowWindow(window, 0)

            # Wait until systray thread terminates
            self.systray_thread.join()
            self.presence.presence_thread.stop()

    # Fetch player presence until it's not empty
    def wait_for_presence(self):
        presence_timeout = Localizer.get_config_value("startup", "presence_timeout")
        presence_timer = 0
        print()
        while self.client.fetch_presence() is None:
            clear_current_line()
            color_print([("Cyan", "["), ("White", str(presence_timer)), ("Cyan", f"] {Localizer.get_localized_text('prints','startup','waiting_for_presence')}")])

            presence_timer += 1
            if presence_timer >= presence_timeout:
                Logger.debug("Timed out waiting for presence!")
                if self.systray is not None:
                    self.systray.exit()
                os._exit(1)

            time.sleep(1) # Wait 1 second

        clear_current_line()
        clear_current_line()

    # Start VALORANT - this will return when the game process is detected
    def start_game(self):
        # Do nothing if game is already running
        if Processes.are_processes_running():
            return

        color_print([("Red", Localizer.get_localized_text("prints", "startup", "starting_valorant"))])

        path = RiotClientServices.get_rcs_path()
        psutil.subprocess.Popen([path, "--launch-product=valorant", "--launch-patchline=live"])
        print()

        # Now wait for the game process to exist...
        launch_timer = 0
        launch_timeout = Localizer.get_config_value("startup", "game_launch_timeout")
        update_time = Localizer.get_config_value("startup", "check_if_updating_time")
        while not Processes.are_processes_running():
            clear_current_line()

            color_print([("Cyan", "["),("White",f"{launch_timer}"),("Cyan", f"] {Localizer.get_localized_text('prints','startup','waiting_for_valorant')}")])
            launch_timer += 1

            # Check if game is updating
            if launch_timer == update_time:
                if Processes.is_updating():
                    clear_current_line()
                    self.presence.update_if_status_changed("Updating") # patching the game
                    input(f"{Style.BRIGHT}{Fore.YELLOW}I think your game is updating. Press {Fore.MAGENTA}Enter{Fore.YELLOW} when you're finished and have launched the game...")
                    launch_timer = 0

            # Check if timeout is exceeded
            if launch_timer >= launch_timeout:
                Logger.debug("Timed out waiting for game!")
                if self.systray is not None:
                    self.systray.exit()
                os._exit(1)

            time.sleep(1) # Wait 1 second

        clear_current_line()