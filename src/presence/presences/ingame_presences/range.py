import time

from ..menu_presences.away import presence as away
from ...presence_utilities import Utilities
from ....localization.localization import Localizer

class Range_Session:

    def __init__(self,ystr_client,client,data,match_id,content_data,config):
        self.ystr_client = ystr_client
        self.client = client
        self.config = config
        self.content_data = content_data
        self.data = data

        data["MapID"] = "/Game/Maps/Poveglia/Range" # hotfix :)
        _, self.mode_name = Utilities.fetch_map_data(data, content_data)

    def main_loop(self):
        presence = self.client.fetch_presence()
        while presence is not None and presence["sessionLoopState"] == "INGAME":
            try:
                presence = self.client.fetch_presence()
                is_afk = presence["isIdle"]
                if is_afk:
                    away(self.ystr_client,self.client,presence,self.content_data,self.config)  
                else:
                    status = f"{self.mode_name} {Utilities.get_party_status(self.data)}"
                    self.ystr_client.update_status(status)

                time.sleep(Localizer.get_config_value("presence_refresh_interval"))
            except:
                return