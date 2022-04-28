import os, requests

from requests.exceptions import ConnectionError, ReadTimeout
from ..utility_functions import Filepath, Logger

class YstrClient:

    HTML_INDICATOR = "!doctype html"
    SECRET_REPLACEMENT = "REDACTED"
    OFFLINE_STATUS = "Offline"
    UPDATING_STATUS = "Updating"
    LIVE_STATUS_PATH = "live_status"
    TIMEOUT = 5 # seconds

    def __init__(self, config):
        self.config = config
        self.config_path = Filepath.get_path(os.path.join(Filepath.get_appdata_folder(), "config.json"))
        self.endpoint = config["endpoint"]
        self.name = config["name"]
        self.secret = config["secret"]

        # Validate existence of configs
        if None in [self.endpoint, self.name, self.secret]:
            raise Exception(f"Missing required config values! Need 'endpoint', 'name', 'secret' to be present in {self.config_path}.")

        # Check if endpoint is reachable and if the call succeeds
        test_response = None
        try:
            test_response = self.update_status("Loading")
            Logger.debug(f"Test call response content: {test_response.content}")
        except ReadTimeout:
            raise Exception(f"Timed out while testing connection to endpoint - the configured credentials or endpoint are probably wrong! Fix them in {self.config_path} and relaunch.")

        if test_response is None or test_response.status_code != 200 or YstrClient.HTML_INDICATOR in str(test_response.content):
            raise Exception(f"Failed to call the endpoint! Check your configured credentials and endpoint (in {self.config_path}) and make sure they're correct.")

    # PUT /live_status
    def update_status(self, status):
        headers = { 'Content-Type': 'application/json' }
        payload = { 'name': self.name, 'status': status, 'secret': self.secret }
        return self.put(YstrClient.LIVE_STATUS_PATH, headers, payload)

    # Make a put call to the configured endpoint at the specified path
    def put(self, path, headers, payload):
        try:
            response = requests.put(f"{self.endpoint}/{path}", headers=headers, json=payload, timeout=YstrClient.TIMEOUT)
            logged_body = payload
            logged_body["secret"] = YstrClient.SECRET_REPLACEMENT
            Logger.debug(f"Request body: {logged_body}")
            Logger.debug(f"Got response: {response.content} with status code {response.status_code}. Headers: {response.headers}")
            return response
        except ConnectionError as e:
            # Connection aborted
            Logger.debug(f"Connection interrupted: {e}")
            return None

    # Mark the player as offline
    def offline(self):
        return self.update_status(YstrClient.OFFLINE_STATUS)
