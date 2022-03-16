from ..presence_utilities import Utilities
from ...localization.localization import Localizer
from valclient.exceptions import PhaseError
from ...utilities.logging import Logger

def presence(ystr_client,client=None,data=None,content_data=None,config=None):  
    try:
        _, mode_name = Utilities.fetch_mode_data(data,content_data)

        status = f"{mode_name} - {Localizer.get_localized_text('presences','client_states','pregame')} {Utilities.get_party_status(data)}"
        ystr_client.update_status(status)
    except PhaseError as e:
        Logger.debug(f"Ran into PhaseError (pregame): {e}")