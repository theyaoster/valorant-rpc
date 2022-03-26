import psutil
import os

class Processes:

    @staticmethod
    def are_processes_running(required_processes=["VALORANT-Win64-Shipping.exe", "RiotClientServices.exe"]):
        processes = []
        for proc in psutil.process_iter():
            processes.append(proc.name())

        return set(required_processes).issubset(processes)

    @staticmethod
    def is_program_already_running():
        processes = []
        for proc in psutil.process_iter():
            processes.append(proc.name())

        if len([proc for proc in processes if proc == "VALORANT-ystr.exe"]) > 2:
            return True

        return False

    @staticmethod
    def is_updating():
        processes = []
        for proc in psutil.process_iter():
            processes.append(proc.name())
        return set(["RiotClientUx.exe", "RiotClientUxRender.exe"]).issubset(processes)