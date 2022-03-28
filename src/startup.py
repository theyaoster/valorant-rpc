from InquirerPy.utils import color_print
from colorama import Fore, Style, Cursor, ansi
import sys, psutil, time, cursor, valclient, ctypes, traceback, os

from .utilities.killable_thread import Thread
from .utilities.config.app_config import Config
from .utilities.processes import Processes
from .utilities.rcs import Riot_Client_Services
from .utilities.systray import Systray
from .utilities.version_checker import Checker
from .utilities.logging import Logger
from .utilities.program_data import Program_Data

from .localization.localization import Localizer

from .presence.presence import Presence

# weird console window management stuff
kernel32 = ctypes.WinDLL('kernel32')
user32 = ctypes.WinDLL('user32')
hWnd = kernel32.GetConsoleWindow()
kernel32.SetConsoleMode(kernel32.GetStdHandle(-10), (0x4|0x80|0x20|0x2|0x10|0x1|0x00|0x100)) # disable inputs to console
kernel32.SetConsoleMode(kernel32.GetStdHandle(-11), 7) # allow for ANSI sequences

# Helper to clear out the current line of stdout
def clear_current_line():
    sys.stdout.write(f"{Cursor.UP()}\r{ansi.clear_line()}")

class Startup:

    def __init__(self):
        if not Processes.is_program_already_running():
            cursor.hide()
            Logger.create_logger()
            Program_Data.update_file_location()

            self.config = Config.fetch_config()
            if self.config["locale"][0] == "":
                config = Localizer.prompt_locale(self.config)
                Config.modify_config(config)
                Systray.restart()

            self.systray = None # This will be set later
            self.installs = Program_Data.fetch_installs()
            Localizer.set_locale(self.config)
            self.config = Config.check_config()
            Localizer.config = self.config

            Logger.debug(self.config)
            self.client = None

            ctypes.windll.kernel32.SetConsoleTitleW(f"VALORANT-ystr {Localizer.get_config_value('version')}")

            try:
                self.presence = Presence(self.config)
                clear_current_line()
            except Exception as e:
                traceback.print_exc()
                raise Exception(f"Error occurred when initializing: {e}")

            self.start_game()

            # If the region is not specified in the config, try to autodetect it (this happens on first launch)
            if Localizer.get_config_value("region", 0) == "":
                color_print([("Red bold", Localizer.get_localized_text("prints", "startup", "autodetect_region"))])

                # Default to NA for now
                client = valclient.Client()
                client.activate()

                # Find the valorant game session and fetch its region
                sessions = client.riotclient_session_fetch_sessions()
                val_session = next(session for _, session in sessions.items() if session["productId"] == "valorant")
                region = next(arg.split("=", 2)[1] for arg in val_session["launchConfiguration"]["arguments"] if "-ares-deployment" in arg) # The value of the ares-deployment arg is the region

                # Update the config to specify the detected region
                self.config[Localizer.get_config_key("region")][0] = region
                Config.modify_config(self.config)
                color_print([("LimeGreen", f"{Localizer.get_localized_text('prints', 'startup', 'autodetected_region')} {Localizer.get_config_value('region', 0)}")])
                Systray.restart()

            self.run()

    def run(self):
        self.presence.update_if_status_changed("Loading")
        Checker.check_version(self.config)

        # Initialize client for VALORANT's client-api
        self.client = valclient.Client(region=Localizer.get_config_value("region", 0))
        self.client.activate()
        self.presence.client = self.client

        # Initialize the systray element
        self.systray = Systray(self.client,self.config)
        self.systray_thread = Thread(target=self.systray.run)
        self.systray_thread.start()

        # Initialize the thread that will poll the player status
        self.wait_for_presence()
        self.presence_thread = Thread(target=self.presence.init_loop,daemon=True)
        self.presence_thread.start()

        color_print([("LimeGreen",f"{Localizer.get_localized_text('prints','startup','startup_successful')}\n")])
        time.sleep(5)
        user32.ShowWindow(hWnd, 0) #hide window

        self.systray_thread.join()
        self.presence_thread.stop()

    # Fetch player presence until it's not empty
    def wait_for_presence(self):
        presence_timeout = Localizer.get_config_value("startup","presence_timeout")
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

        path = Riot_Client_Services.get_rcs_path()
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