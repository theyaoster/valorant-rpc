from .ingame_presences.session import Game_Session
from .ingame_presences.range import Range_Session
from valclient.exceptions import PhaseError
from ...utilities.logging import Logger

def presence(ystr_client,client=None,data=None,content_data=None,config=None):
    try:
        coregame = client.coregame_fetch_player()

        if coregame is not None:
            match_id = coregame["MatchID"]
            if data["provisioningFlow"] != "ShootingRange":
                try:
                    session = Game_Session(ystr_client,client,data,match_id,content_data,config)
                    session.main_loop()
                except:
                    pass
            else:
                session = Range_Session(ystr_client,client,data,match_id,content_data,config)
                session.main_loop()

    except PhaseError as e:
        Logger.debug(f"Ran into PhaseError (in-game): {e}")
