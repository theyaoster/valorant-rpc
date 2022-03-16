from ...localization.localization import Localizer

def presence(ystr_client,client=None,data=None,content_data=None,config=None):
    status = Localizer.get_localized_text("presences","startup","loading")
    ystr_client.update_status(status)