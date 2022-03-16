from ....localization.localization import Localizer
from ...presence_utilities import Utilities

def presence(ystr_client,client=None,data=None,content_data=None,config=None):
    _, mode_name = Utilities.fetch_mode_data(data,content_data)
    status = f"{mode_name} - {Localizer.get_localized_text('presences','client_states','away')} {Utilities.get_party_status(data)}"
    ystr_client.update_status(status)
