import time

from ...presence_utilities import Utilities
from ..menu_presences.away import presence as away
from ....localization.localization import Localizer
from valclient.exceptions import PhaseError

class Game_Session:

    def __init__(self,ystr_client,client,data,match_id,content_data,config):
        self.ystr_client = ystr_client
        self.client = client
        self.config = config
        self.content_data = content_data
        self.data = data
        self.mode_name = ""

        self.build_static_states()

    def build_static_states(self):
        # generate agent, map etc.
        presence = self.client.fetch_presence()
        _, self.mode_name = Utilities.fetch_mode_data(presence,self.content_data)

    def main_loop(self):
        presence = self.client.fetch_presence()
        while presence is not None and presence["sessionLoopState"] == "INGAME":
            presence = self.client.fetch_presence()
            is_afk = presence["isIdle"]
            if is_afk:
                away(self.ystr_client,self.client,presence,self.content_data,self.config)  
            else:
                my_score,other_score = presence["partyOwnerMatchScoreAllyTeam"],presence["partyOwnerMatchScoreEnemyTeam"]

                status = f"{self.mode_name} - {my_score} to {other_score} {Utilities.get_party_status(self.data)}"
                self.ystr_client.update_status(status)

            time.sleep(Localizer.get_config_value("presence_refresh_interval"))