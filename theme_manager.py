import json
import os
import winreg

class ThemeManager:
    def __init__(self):
        self.themes = {
            'Light': {
                'bg': '#ffffff',
                'fg': '#000000',
                'selectbg': '#0078d7',
                'selectfg': '#ffffff',
                'textbg': '#ffffff',
                'textfg': '#000000',
                'buttonbg': '#f0f0f0',
                'buttonfg': '#000000',
                'framebg': '#f5f5f5',
                'inputbg': '#ffffff',
                'inputfg': '#000000'
            },
            'Dark': {
                'bg': '#1e1e1e',
                'fg': '#ffffff',
                'selectbg': '#264f78',
                'selectfg': '#ffffff',
                'textbg': '#2d2d2d',
                'textfg': '#ffffff',
                'buttonbg': '#333333',
                'buttonfg': '#ffffff',
                'framebg': '#252526',
                'inputbg': '#3c3c3c',
                'inputfg': '#ffffff'
            }
        }
        self.current_theme = 'Light'
        self.load_custom_themes()

    def load_custom_themes(self):
        """
        tries to load custom themes from the registry and a local JSON file.
        """
        try:
            with winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"SOFTWARE\MyBIOSManager", 0, winreg.KEY_READ) as key:
                themes_json, _ = winreg.QueryValueEx(key, "custom_themes")
                custom_themes = json.loads(themes_json)
                self.themes.update(custom_themes)
        except FileNotFoundError:
            pass
        except Exception as e:
            print(f"Error loading custom themes from registry: {e}")

        try:
            if os.path.exists('custom_themes.json'):
                with open('custom_themes.json', 'r') as f:
                    file_themes = json.load(f)
                    self.themes.update(file_themes)
        except Exception as e:
            print(f"Error loading custom themes from JSON file: {e}")

    def save_custom_themes(self):
        """
        save custom themes to the registry and a local JSON file.
        """
        try:
            custom_themes = {k: v for k, v in self.themes.items() if k not in ['Light', 'Dark']}
            try:
                with winreg.CreateKey(winreg.HKEY_CURRENT_USER, r"SOFTWARE\MyBIOSManager") as key:
                    json_str = json.dumps(custom_themes, indent=4)
                    winreg.SetValueEx(key, "custom_themes", 0, winreg.REG_SZ, json_str)
            except Exception as e:
                print(f"Error saving custom themes to registry: {e}")
            try:
                with open('custom_themes.json', 'w') as f:
                    json.dump(custom_themes, f, indent=4)
            except Exception as e:
                print(f"Error saving custom themes to JSON file: {e}")
        except Exception as e:
            print(f"Error preparing custom themes for save: {e}")
