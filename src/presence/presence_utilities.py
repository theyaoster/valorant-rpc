from ..localization.localization import Localizer

class Utilities:

    @staticmethod
    def build_party_state(data):
        party_state = Localizer.get_localized_text("presences","party_states","solo")
        if data["partySize"] > 1:
            party_state = Localizer.get_localized_text("presences","party_states","in_party")
        elif data["partyAccessibility"] == "OPEN":
            party_state = Localizer.get_localized_text("presences","party_states","open")

        party_size = [data["partySize"],data["maxPartySize"]] if data["partySize"] > 1 else [1, 1]
        if party_size is not None:
            if party_size[0] == 0:
                party_size[0] = 1
            if party_size[1] < 1:
                party_size[1] = 1
        return party_state, party_size

    @staticmethod
    def fetch_map_data(coregame_data,content_data):
        for gmap in content_data["maps"]:
            if gmap["path"] == coregame_data["MapID"]:
                return gmap["display_name"], gmap["display_name_localized"]
        return "", ""

    @staticmethod
    def fetch_mode_data(data, content_data):
        image = f"mode_{data['queueId'] if data['queueId'] in content_data['modes_with_icons'] else 'discovery'}"
        mode_name = content_data['queue_aliases'][data['queueId']] if data["queueId"] in content_data["queue_aliases"].keys() else "Custom"

        # For some reason, Custom games have a queueId of onefa, same as Replication...
        if "Custom" in data['provisioningFlow'] and "Custom" not in mode_name:
            mode_name = "Custom"
            data["queueId"] = "custom"

        mode_name = Utilities.localize_content_name(mode_name, "presences", "modes", data["queueId"])
        return image,mode_name

    @staticmethod
    def localize_content_name(default,*keys):
        localized = Localizer.get_localized_text(*keys)
        if localized is not None:
            return localized
        return default

    @staticmethod
    def get_party_status(data):
        size = Utilities.build_party_state(data)[1]
        if (size[0] == 1):
            return "(solo)"
        else:
            return f"(in a {size[0]}-stack)"
