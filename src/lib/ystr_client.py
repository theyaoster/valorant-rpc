import os, requests, copy

from requests.exceptions import ConnectionError, ReadTimeout
from ..utility_functions import Filepath, Logger
from ..config.constants import Constants

class YstrClient:

    HTML_INDICATOR = "!doctype html"
    SECRET_REPLACEMENT = "REDACTED"
    TIMEOUT = 5 # seconds

    def __init__(self, config):
        self.config = config
        self.config_path = Filepath.get_path(os.path.join(Filepath.get_appdata_folder(), Constants.CONFIG_FILENAME))
        self.endpoints = config[Constants.ENDPOINTS]

        # Validate existence of configs
        if self.endpoints is None or not bool(self.endpoints):
            raise Exception(f"Missing endpoints in config! Need {Constants.ENDPOINTS} to be present in {self.config_path}.")

        # Check if endpoint is reachable and if the call succeeds
        test_responses = None
        try:
            test_responses = self.update_status(Constants.LOADING_STATUS)
        except ReadTimeout:
            raise Exception(f"Timed out while testing connection to endpoint - the configured credentials or endpoint are probably wrong! Fix them in {self.config_path} and relaunch.")

        if test_responses is None or any(response is None or response.status_code != 200 or YstrClient.HTML_INDICATOR in str(response.content) for response in test_responses):
            raise Exception(f"Failed to call one or more endpoints! Check your configured credentials and endpoint (in {self.config_path}) and make sure they're correct. Response: {test_responses}")

    # PUT /live_status
    def update_status(self, status):
        responses = []
        for endpoint, payload in self.endpoints.items():
            payload_copy = copy.deepcopy(payload)
            placeholder_found = False
            for key, val in payload_copy.items():
                if val == Constants.STATUS_PLACEHOLDER:
                    payload_copy[key] = status
                    placeholder_found = True

            if not placeholder_found:
                raise ValueError(f"Could not find placeholder in payload: {payload_copy}")

            responses.append(self.call(endpoint, requests.put, Constants.LIVE_STATUS_PATH, payload_copy))

        return responses

    # Generic method for making an http call to the configured endpoint
    def call(self, endpoint, method, path, payload):
        logged_body = payload.copy()
        if Constants.SECRET in logged_body:
            logged_body[Constants.SECRET] = YstrClient.SECRET_REPLACEMENT

        method_name = method.__name__.upper()
        Logger.debug(f"{method_name} /{path} request body: {logged_body}")

        try:
            response = method(f"{endpoint}/{path}", headers={ 'Content-Type': 'application/json' }, json=payload, timeout=YstrClient.TIMEOUT)

            Logger.debug(f"{method_name} /{path} completed {response.status_code}.")

            return response
        except ConnectionError as e:
            # Connection aborted
            Logger.debug(f"Connection error while calling {method_name} /{path}: {e}")
        except ReadTimeout as e:
            # Connection timed out
            Logger.debug(f"Timed out while calling {method_name} /{path}: {e}")

        return None

    # Mark the player as offline
    def offline(self):
        return self.update_status(Constants.OFFLINE_STATUS)
