from InquirerPy.utils import color_print
import ctypes, traceback

from ..localization.localization import Localizer

kernel32 = ctypes.WinDLL('kernel32')
user32 = ctypes.WinDLL('user32')
hWnd = kernel32.GetConsoleWindow()

def handle_error(error=None):
    user32.ShowWindow(hWnd, 1)
    kernel32.SetConsoleMode(kernel32.GetStdHandle(-10), (0x4|0x80|0x20|0x2|0x10|0x1|0x40|0x100))
    color_print([("Red bold", Localizer.get_localized_text("prints", "errors", "error_message"))])
    print()
    if error is None:
        traceback.print_exc()
    else:
        color_print([("Red bold", str(error))])
    print()
    input(Localizer.get_localized_text("prints", "errors", "exit"))