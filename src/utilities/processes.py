import psutil

from .logging import Logger
from .config.constants import Constants

# Helper to get list of running processes
def running_processes():
    processes = []
    for proc in psutil.process_iter():
        try:
            processes.append(proc.name())
        except psutil.NoSuchProcess as e:
            Logger.debug(f"Failed to find running process: {e}")
            continue

    return processes

class Processes:

    @staticmethod
    def are_processes_running(processes=Constants.GAME_EXES):
        return set(processes).issubset(running_processes())

    @staticmethod
    def is_program_already_running():
        return running_processes().count(Constants.PROGRAM_EXE) > Constants.PROGRAM_PROC_COUNT

    @staticmethod
    def is_updating():
        return Processes.are_processes_running(Constants.GAME_CLIENT_UX_EXES)