import time, os
from valclient.exceptions import ResponseError

from .utility_functions import ErrorHandling, Logger, ContentLoader
from .localization.localization import Localizer
from .lib.killable_thread import KillableThread
from .lib.ystr_client import YstrClient

# A thread that polls for contract changes
class ContractManager:

    def __init__(self, valclient, config):
        self.config = config
        self.client = valclient
        self.ystr_client = YstrClient(self.config)
        ContentLoader.cache_contracts()
        self.equipped_contract = self.active_contract()
        self.current_contract = self.ystr_client.get_contract()

        # Check for discrepancy between selected contract and active contract - favor the selected one
        if self.current_contract != self.equipped_contract:
            Logger.debug(f"Remote contract is '{self.current_contract}' while locally, it is '{self.equipped_contract}'. Overriding to be '{self.current_contract}'.")

            self.client.contracts_activate(ContentLoader.get_contract(self.current_contract))
            self.equipped_contract = self.current_contract

    # Poll contract in remote config
    def poll_loop(self):
        sleep_duration = int(Localizer.get_config_value("contract_poll_interval"))
        while True:
            contract = self.ystr_client.get_contract()
            if contract != self.current_contract:
                Logger.debug(f"Detected new set contract - activating '{contract}'.")

                self.client.contracts_activate(ContentLoader.get_contract(contract))
                self.current_contract = contract

            time.sleep(sleep_duration)

    # Sync local contract changes
    def sync_loop(self):
        sleep_duration = int(Localizer.get_config_value("contract_sync_interval"))
        while True:
            contract = self.active_contract()
            if contract != self.equipped_contract and contract is not None:
                Logger.debug(f"Detected local contract change to {contract}.")
                self.ystr_client.update_contract(contract)
                self.equipped_contract = contract

            time.sleep(sleep_duration)

    # Start the thread to continuously poll game presence
    def start_poll_thread(self):
        try:
            self.poll_thread = KillableThread(target=self.poll_loop, daemon=True)
            self.poll_thread.start()
        except Exception as e:
            Logger.debug(f"Error starting contract poll thread: {e}")

            ErrorHandling.handle_error()
            self.kill_contract_thread("poll")

    # Start the thread to sync local contract changes
    def start_sync_thread(self):
        try:
            self.sync_thread = KillableThread(target=self.sync_loop, daemon=True)
            self.sync_thread.start()
        except Exception as e:
            Logger.debug(f"Error starting contract sync thread: {e}")

            ErrorHandling.handle_error()
            self.kill_contract_thread("sync")

    def active_contract(self):
        try:
            contract_data = self.client.contracts_fetch()
            return next((agent for agent in ContentLoader.CONTENT_CACHE.contracts if ContentLoader.CONTENT_CACHE.contracts[agent] == contract_data["ActiveSpecialContract"]), None)
        except ResponseError as e:
            Logger.debug(f"Error while fetching current contract: {e}")
            return None


    # Helper for killing this thread while notifying the user and the web service
    def kill_contract_thread(self, name, message=""):
        Logger.debug(f"Killing contract {name} thread due to: {message}")

        self.ystr_client.offline()
        os._exit(1)