from InquirerPy.utils import color_print
from InquirerPy import inquirer

from .app_config import Config
from ...localization.localization import Localizer

MAIN_SECTION = "main"
BACK_VALUE = "back"
UNMODIFIABLE = ["version", "presence_refresh_interval", "startup"]

class ConfigEditor:

    def __init__(self):
        self.config = Config.fetch_config()

        self.config_menu(MAIN_SECTION, self.config)

    def config_menu(self, section, choices, callback=None, callback_args=None):
        prompt_choices = [{ "name": "Go Back" if section != MAIN_SECTION else "Save Settings", "value": BACK_VALUE }]

        for setting, value in choices.items():
            if setting in UNMODIFIABLE:
                continue
            setting_value = f" ([{value[0]}...])" if isinstance(value, list) else f" ({value})" if not isinstance(value, dict) else " (\{...\})"
            prompt_choices.append({ "name": setting + setting_value, "value": setting })

        choice = inquirer.select(
            message=f"[{section}] {Localizer.get_localized_text('prints','config_modification','select_option')}",
            choices=prompt_choices,
            pointer=">"
        )
        choice = choice.execute()

        if choice == BACK_VALUE:
            if section != MAIN_SECTION:
                callback(*callback_args)
            elif callback is None:
                Config.modify_config(self.config)
                color_print([("LimeGreen", Localizer.get_localized_text("prints","config_modification","config_saved"))])
        else:
            if isinstance(choices[choice], dict):
                self.config_menu(choice, choices[choice], callback=self.config_menu,callback_args=(section, choices, callback, callback_args))
            else:
                if choice == Localizer.get_config_key("locale"):
                    # translate config
                    new_locale = self.config_set(choice, choices[choice])[0]
                    self.config = Config.localize_config(self.config,True)
                    self.config["locale"][0] = new_locale
                    Localizer.locale = new_locale
                    self.config = Config.localize_config(self.config,False)
                    Localizer.config = self.config
                else:
                    choices[choice] = self.config_set(choice, choices[choice])

                self.config_menu(section, choices, callback, callback_args)

    @staticmethod
    def config_set(name, option):
        if type(option) is str:
            choice = inquirer.text(
                message=f"{Localizer.get_localized_text('prints','config_modification','set_prompt')} {name} (expecting str)",
                default=str(option),
                validate=lambda result: not result.isdigit(),
                filter=lambda result: str(result)
            )
            choice = choice.execute()
            return choice

        if type(option) is int:
            choice = inquirer.text(
                message=f"{Localizer.get_localized_text('prints','config_modification','set_prompt')} {name} (expecting int)",
                default=str(option),
                validate=lambda result: result.isdigit(),
                filter=lambda result: int(result)
            )
            choice = choice.execute()
            return choice

        if type(option) is bool:
            choice = inquirer.select(
                message=f"{Localizer.get_localized_text('prints','config_modification','set_prompt')} {name}",
                default=option,
                choices=[{"name": "true", "value": True},
                         {"name": "false", "value": False}],
                pointer=">"
            )
            choice = choice.execute()
            return choice

        if type(option) is list:
            current = option[0]
            options = option[1]
            choice = inquirer.select(
                message=f"{Localizer.get_localized_text('prints','config_modification','set_prompt')} {name}",
                default=current,
                choices={option:option for option in options},
                pointer=">"
            )
            choice = choice.execute()
            option[0] = choice
            return option