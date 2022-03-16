from ...presence_utilities import Utilities
from ....localization.localization import Localizer

from .away import presence as away

def presence(ystr_client,client=None,data=None,content_data=None,config=None):
    is_afk = data["isIdle"]
    if is_afk:
        away(ystr_client,client,data,content_data,config)  
     
    else:
        _, mode_name = Utilities.fetch_mode_data(data,content_data)

        status = f"{mode_name} - {Localizer.get_localized_text('presences','client_states','menu')} {Utilities.get_party_status(data)}"
        ystr_client.update_status(status)