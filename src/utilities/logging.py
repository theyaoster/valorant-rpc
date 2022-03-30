import logging, os
from .filepath import Filepath

class Logger:

    @staticmethod
    def create_logger():
        # To not get swamped with (mostly) irrelevant log messages...
        logging.getLogger("urllib3").setLevel(logging.WARNING)
        logging.getLogger("PIL.Image").setLevel(logging.WARNING)

        # Create logger
        os.makedirs(Filepath.get_path(Filepath.get_appdata_folder()), exist_ok=True)
        logging.basicConfig(filename=Filepath.get_path(os.path.join(Filepath.get_appdata_folder(), 'ystr.log')),
                            filemode='w+',
                            format='%(asctime)s.%(msecs)d %(name)s %(levelname)s %(message)s',
                            datefmt='%H:%M:%S',
                            level=logging.DEBUG)

    @staticmethod
    def debug(data):
        logger = logging.getLogger('ystr')
        logger.debug(data)