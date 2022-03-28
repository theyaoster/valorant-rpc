import iso8601
from ..utilities.logging import Logger
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
    def iso8601_to_epoch(time):
        if time == "0001.01.01-00.00.00":
            return None
        split = time.split("-")
        split[0] = split[0].replace(".","-")
        split[1] = split[1].replace(".",":")
        split = "T".join(i for i in split)
        split = iso8601.parse_date(split).timestamp() #converts iso8601 to epoch
        return split

    @staticmethod
    def fetch_rank_data(client,content_data):
        try:
            mmr = client.fetch_mmr()["QueueSkills"]["competitive"]["SeasonalInfoBySeasonID"][content_data["season"]["season_uuid"]]
        except:
            return "rank_0","Rank not found"
        rank_data = {}
        for tier in content_data["comp_tiers"]:
            if tier["id"] == mmr["CompetitiveTier"]:
                rank_data = tier
        rank_image = f"rank_{rank_data['id']}"
        rank_text = f"{rank_data['display_name_localized']} - {mmr['RankedRating']}{Localizer.get_localized_text('presences','leveling','ranked_rating')}" + (f" // #{mmr['LeaderboardRank']}" if mmr['LeaderboardRank'] != 0 else "")

        return rank_image, rank_text

    @staticmethod
    def fetch_map_data(coregame_data,content_data):
        for gmap in content_data["maps"]:
            if gmap["path"] == coregame_data["MapID"]:
                return gmap["display_name"], gmap["display_name_localized"]
        return "", ""

    @staticmethod
    def fetch_agent_data(uuid,content_data):
        for agent in content_data["agents"]:
            if agent["uuid"] == uuid:
                agent_image = f"agent_{agent['display_name'].lower().replace('/','')}"
                agent_name = agent['display_name_localized']
                return agent_image, agent_name
        return "rank_0","?"

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
    def get_content_preferences(client,pref,presence,player_data,coregame_data,content_data):
        if pref == Localizer.get_localized_text("config", "rank"):
            return Utilities.fetch_rank_data(client,content_data)
        if pref == Localizer.get_localized_text("config", "map"):
            gmap = Utilities.fetch_map_data(coregame_data,content_data)
            return f"splash_{gmap[0].lower()}", gmap[1]
        if pref == Localizer.get_localized_text("config", "agent"):
            return Utilities.fetch_agent_data(player_data["CharacterID"],content_data)

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
