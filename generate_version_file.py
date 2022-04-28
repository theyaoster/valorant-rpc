import time

from src.config.constants import Constants
from src.utility_functions import Filepath

current_time = int(time.time())

version_file_content = f"""VSVersionInfo(
    ffi=FixedFileInfo(
        filevers={Constants.VERSION_NUMBERS},
        prodvers={Constants.VERSION_NUMBERS},
        mask=0x3f,
        flags=0x0,
        OS=0x4,
        fileType=0x1,
        subtype=0x0,
        date=({current_time}, 0)
    ),
    kids=[
        StringFileInfo(
            [
                StringTable(
                    u'040904B0',
                    [
                        StringStruct(u'CompanyName', u'{Constants.WHOAMI}'),
                        StringStruct(u'FileDescription', u'{Constants.PROGRAM_NAME}'),
                        StringStruct(u'FileVersion', u'{Constants.VERSION_STR}'),
                        StringStruct(u'InternalName', u'{Constants.PROGRAM_NAME}'),
                        StringStruct(u'LegalCopyright', u'{Constants.WHOAMI}'),
                        StringStruct(u'OriginalFilename', u'{Constants.PROGRAM_EXE}'),
                        StringStruct(u'ProductName', u'{Constants.PROGRAM_NAME}'),
                        StringStruct(u'ProductVersion', u'{Constants.VERSION_STR}')
                    ]
                )
            ]
        ),
        VarFileInfo(
            [
                VarStruct(u'Translation', [1033, 1200])
            ]
        )
    ]
)
"""

with open(Filepath.get_path(Constants.VERSION_FILENAME), 'w') as version_file:
    version_file.write(version_file_content)

print(f"Generated {Constants.VERSION_FILENAME}.\n")