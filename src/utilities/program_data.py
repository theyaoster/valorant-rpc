import os, sys, json
from InquirerPy.utils import color_print

from .filepath import Filepath

class ProgramData:

    installs_path = os.path.expandvars("%PROGRAMDATA%\\valorant-tools\\installs.json")

    @staticmethod
    def update_file_location():
        ProgramData.check_for_folder()
        if getattr(sys, 'frozen', False):
            path = sys.executable
        else:
            color_print([("Yellow","running in a testing environment, cannot update installation path")])
            path = None

        if path is not None:
            installs = ProgramData.fetch_installs()
            installs["VALORANT-ystr"] = path
            ProgramData.modify_installs(installs)


    @staticmethod
    def fetch_installs():
        try:
            with open(ProgramData.installs_path) as f:
                installs = json.load(f)
                return installs
        except:
            return ProgramData.create_installs_file()

    @staticmethod
    def modify_installs(payload):
        with open(ProgramData.installs_path, "w") as f:
            json.dump(payload, f)

        return ProgramData.fetch_installs()

    @staticmethod
    def create_installs_file():
        with open(ProgramData.installs_path, "w") as f:
            payload = {}
            json.dump(payload, f)

        return ProgramData.fetch_installs()

    @staticmethod
    def check_for_folder():
        programdata_folder = Filepath.get_programdata_folder()
        if not os.path.isdir(programdata_folder):
            os.makedirs(programdata_folder)