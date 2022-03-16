import os, requests, logging

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
            raise f"Missing required config values! Need 'endpoint', 'name', 'secret' to be present in {self.config_path}."
        
    def update_status(self, status):
        payload = { 'name': self.name, 'status': status, 'secret': self.secret }
        headers = { 'Content-Type': 'application/json' }
        response = requests.put(f"{self.endpoint}/live_status", headers=headers, json=payload)
        Logger.debug(f"Request headers: {response.request.headers}, body: {response.request.body}")
        Logger.debug(f"Got response: {response.content} with status code {response.status_code}. Headers: {response.headers}")

    def offline(self):
        self.update_status("Offline")
