import os, requests

from requests.exceptions import ConnectionError
from .filepath import Filepath
from .logging import Logger

class YstrClient:

    def __init__(self, config):
        self.config = config
        self.config_path = Filepath.get_path(os.path.join(Filepath.get_appdata_folder(), "config.json"))
        self.endpoint = config["endpoint"]
        self.name = config["name"]
        self.secret = config["secret"]
        if self.endpoint is None or self.name is None or self.secret is None:
            raise Exception(f"Missing required config values! Need 'endpoint', 'name', 'secret' to be present in {self.config_path}.")

        test_response = self.update_status("Loading")
        if test_response is None or test_response.status_code != 200:
            raise Exception(f"Failed to call the endpoint! Check your configured credentials and endpoint to make sure they're correct.")

    def update_status(self, status):
        headers = { 'Content-Type': 'application/json' }
        payload = { 'name': self.name, 'status': status, 'secret': self.secret }
        return self.put("live_status", headers, payload)

    def put(self, path, headers, payload):
        try:
            response = requests.put(f"{self.endpoint}/{path}", headers=headers, json=payload)
            Logger.debug(f"Request headers: {response.request.headers}, body: {response.request.body}")
            Logger.debug(f"Got response: {response.content} with status code {response.status_code}. Headers: {response.headers}")
            return response
        except ConnectionError as e:
            # Connection aborted
            Logger.debug(f"Connection interrupted: {e}")
            return None

    def offline(self):
        return self.update_status("Offline")
