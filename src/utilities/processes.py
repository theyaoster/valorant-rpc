import psutil

from ..utilities.logging import Logger

# Helper that iterates over active processes while catching any psutil errors,
# which would cause the program to hang while starting the game
def process_iter_with_handling():
    for proc in psutil.process_iter():
        try:
            yield proc.name()
        except Exception as e:
            Logger.debug(f"Error occurred while iterating over running processes: {e}")

class Processes:

    @staticmethod
    def are_processes_running(required_processes=["VALORANT-Win64-Shipping.exe", "RiotClientServices.exe"]):
        return set(required_processes).issubset(process_iter_with_handling())

    @staticmethod
    def is_program_already_running(program_name="VALORANT-ystr.exe"):
        return len([proc_name for proc_name in process_iter_with_handling() if proc_name == program_name]) > 2

    @staticmethod
    def is_updating(updating_processes=["RiotClientUx.exe", "RiotClientUxRender.exe"]):
        return set(updating_processes).issubset(process_iter_with_handling())