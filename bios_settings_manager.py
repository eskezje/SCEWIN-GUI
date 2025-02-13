import tkinter as tk
from tkinter import ttk, filedialog, messagebox, colorchooser
import re
from typing import List, Optional
import winreg
import json
from models import BIOSSetting
from theme_manager import ThemeManager

class BIOSSettingsManager:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("scewinGUI")
        self.root.geometry("1200x800")

        # Initialize theme manager
        self.theme_manager = ThemeManager()

        # load the last selected theme from the registry, if available
        self._load_theme_from_registry()

        # configure initial styles
        self.style = ttk.Style()
        self.style.theme_use('default')

        # storing the data
        self.settings: List[BIOSSetting] = []
        self.original_lines: List[str] = []
        self.current_file: Optional[str] = None

        # lovely regex
        self.re_comment = re.compile(r'(\s*)(//.*)?$')
        self.re_setup_question = re.compile(r'^Setup\s+Question\s*=\s*(.*)', re.IGNORECASE)
        self.re_help_string = re.compile(r'^Help\s+String\s*=\s*(.*)', re.IGNORECASE)
        self.re_token = re.compile(r'^Token\s*=\s*(.*)', re.IGNORECASE)
        self.re_offset = re.compile(r'^Offset\s*=\s*(.*)', re.IGNORECASE)
        self.re_width = re.compile(r'^Width\s*=\s*(.*)', re.IGNORECASE)
        self.re_bios_default = re.compile(r'^BIOS\s+Default\s*=\s*(.*)', re.IGNORECASE)
        self.re_options = re.compile(r'^Options\s*=\s*(.*)', re.IGNORECASE)
        self.re_value = re.compile(r'^Value\s*=\s*(.*)', re.IGNORECASE)

        self._setup_gui()
        self._apply_theme()

    def _load_theme_from_registry(self):
        """
        reads the 'current_theme' from the windows registry and loads it
        """
        try:
            with winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"SOFTWARE\MyBIOSManager", 0, winreg.KEY_READ) as key:
                theme_name, _ = winreg.QueryValueEx(key, "current_theme")
                if theme_name in self.theme_manager.themes:
                    self.theme_manager.current_theme = theme_name
        except FileNotFoundError:
            pass
        except Exception as e:
            print(f"Error loading theme from registry: {e}")

    def _save_theme_to_registry(self, theme_name: str):
        """
        saves the current theme to windows registry
        """
        try:
            with winreg.CreateKey(winreg.HKEY_CURRENT_USER, r"SOFTWARE\MyBIOSManager") as key:
                winreg.SetValueEx(key, "current_theme", 0, winreg.REG_SZ, theme_name)
        except Exception as e:
            print(f"Error saving theme to registry: {e}")

    def _setup_gui(self):
        """Setup the GUI components for the ScewinGUI manager"""
        self.menu_bar = tk.Menu(self.root)
        self.root.config(menu=self.menu_bar)

        # FILE MENU
        self.file_menu = tk.Menu(self.menu_bar, tearoff=0)
        self.menu_bar.add_cascade(label="File", menu=self.file_menu)
        self.file_menu.add_command(label="Open...", command=self._load_file)
        self.file_menu.add_command(label="Save...", command=self._save_file)
        self.file_menu.add_separator()
        self.file_menu.add_command(label="Exit", command=self.root.quit)

        # VIEW MENU
        self.view_menu = tk.Menu(self.menu_bar, tearoff=0)
        self.menu_bar.add_cascade(label="View", menu=self.view_menu)

        # THEME SUBMENU
        self.theme_menu = tk.Menu(self.view_menu, tearoff=0)
        self.view_menu.add_cascade(label="Theme", menu=self.theme_menu)
        self.theme_var = tk.StringVar(value=self.theme_manager.current_theme)
        for theme_name in self.theme_manager.themes.keys():
            self.theme_menu.add_radiobutton(
                label=theme_name,
                variable=self.theme_var,
                value=theme_name,
                command=self._apply_theme
            )

        # SETTINGS MENU
        self.settings_menu = tk.Menu(self.menu_bar, tearoff=0)
        self.menu_bar.add_cascade(label="Settings", menu=self.settings_menu)
        self.settings_menu.add_command(label="Custom Theme...", command=self._show_theme_editor)

        # TOP FRAME
        self.top_frame = ttk.Frame(self.root)
        self.top_frame.pack(fill=tk.X, padx=5, pady=5)
        ttk.Button(self.top_frame, text="Load File", command=self._load_file).pack(side=tk.LEFT, padx=5)
        ttk.Button(self.top_frame, text="Save File", command=self._save_file).pack(side=tk.LEFT, padx=5)

        # SERACH FRAME
        search_frame = ttk.Frame(self.top_frame)
        search_frame.pack(side=tk.RIGHT, padx=5)
        ttk.Label(search_frame, text="Search:").pack(side=tk.LEFT)
        self.search_var = tk.StringVar()
        self.search_var.trace('w', self._filter_settings)
        ttk.Entry(search_frame, textvariable=self.search_var, width=30).pack(side=tk.LEFT, padx=5)

        # MAIN FRAME
        self.main_frame = ttk.PanedWindow(self.root, orient=tk.HORIZONTAL)
        self.main_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # LEFT FRAME: LIST OF SETTINGS
        list_frame = ttk.Frame(self.main_frame)
        self.main_frame.add(list_frame, weight=1)
        self.settings_list = ttk.Treeview(list_frame, columns=('value',), show='tree')
        self.settings_list.heading('#0', text='Setting')
        self.settings_list.heading('value', text='Current Value')
        self.settings_list.pack(fill=tk.BOTH, expand=True, side=tk.LEFT)
        scrollbar = ttk.Scrollbar(list_frame, orient="vertical", command=self.settings_list.yview)
        scrollbar.pack(side=tk.RIGHT, fill="y")
        self.settings_list.configure(yscrollcommand=scrollbar.set)

        # RIGHT PANEL: DETAILS OF SELECTED SETTING
        details_frame = ttk.Frame(self.main_frame)
        self.main_frame.add(details_frame, weight=2)
        self.details_text = tk.Text(details_frame, wrap=tk.WORD, height=10, state=tk.DISABLED)
        self.details_text.pack(fill=tk.X, padx=5, pady=5)
        self.options_frame = ttk.LabelFrame(details_frame, text="Options")
        self.options_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        self.settings_list.bind('<<TreeviewSelect>>', self._on_setting_select)

    def _show_theme_editor(self):
        theme_editor = tk.Toplevel(self.root)
        theme_editor.title("Theme Editor")
        theme_editor.geometry("400x500")
        
        # SELEC THEME
        select_frame = ttk.LabelFrame(theme_editor, text="Select Theme")
        select_frame.pack(fill=tk.X, padx=5, pady=5)
        theme_var = tk.StringVar(value=self.theme_manager.current_theme)
        theme_combo = ttk.Combobox(select_frame, textvariable=theme_var,
                                   values=list(self.theme_manager.themes.keys()))
        theme_combo.pack(padx=5, pady=5)
        
        # SETTING UP CUSTOM THEME
        colors_frame = ttk.LabelFrame(theme_editor, text="Colors")
        colors_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        color_vars = {}
        def update_color(key):
            color = colorchooser.askcolor(color=color_vars[key].get())[1]
            if color:
                color_vars[key].set(color)
        def load_theme_colors(*args):
            theme = self.theme_manager.themes[theme_var.get()]
            for key, var in color_vars.items():
                var.set(theme[key])
        def save_as_new_theme():
            name = theme_name_var.get().strip()
            if not name:
                messagebox.showerror("Error", "Please enter a theme name")
                return
            new_theme = {key: var.get() for key, var in color_vars.items()}
            self.theme_manager.themes[name] = new_theme
            self.theme_manager.save_custom_themes()
            self.theme_menu.add_radiobutton(
                label=name,
                variable=self.theme_var,
                value=name,
                command=self._apply_theme
            )
            theme_combo['values'] = list(self.theme_manager.themes.keys())
            messagebox.showinfo("Success", f"Theme '{name}' saved successfully")
        for key in ['bg', 'fg', 'selectbg', 'selectfg', 'textbg', 'textfg']:
            frame = ttk.Frame(colors_frame)
            frame.pack(fill=tk.X, padx=5, pady=2)
            ttk.Label(frame, text=f"{key}:").pack(side=tk.LEFT)
            color_vars[key] = tk.StringVar()
            ttk.Entry(frame, textvariable=color_vars[key], width=10).pack(side=tk.LEFT, padx=5)
            ttk.Button(frame, text="Choose...", command=lambda k=key: update_color(k)).pack(side=tk.LEFT)
        save_frame = ttk.LabelFrame(theme_editor, text="Save as New Theme")
        save_frame.pack(fill=tk.X, padx=5, pady=5)
        theme_name_var = tk.StringVar()
        ttk.Entry(save_frame, textvariable=theme_name_var).pack(side=tk.LEFT, padx=5, pady=5, fill=tk.X, expand=True)
        ttk.Button(save_frame, text="Save", command=save_as_new_theme).pack(side=tk.LEFT, padx=5, pady=5)
        theme_combo.bind('<<ComboboxSelected>>', load_theme_colors)
        load_theme_colors()

    def _apply_theme(self):
        theme_name = self.theme_var.get()
        theme = self.theme_manager.themes[theme_name]
        self.theme_manager.current_theme = theme_name
        # tryint to save the theme to the registry
        self._save_theme_to_registry(theme_name)
        self.root.configure(bg=theme['bg'])
        style = self.style
        style.configure('.',
                        background=theme['bg'],
                        foreground=theme['fg'],
                        fieldbackground=theme['inputbg'],
                        troughcolor=theme['bg'],
                        selectbackground=theme['selectbg'],
                        selectforeground=theme['selectfg'])
        style.configure('TFrame', background=theme['framebg'])
        style.configure('TLabelframe', background=theme['framebg'])
        style.configure('TLabelframe.Label', background=theme['framebg'], foreground=theme['fg'])
        style.configure('TButton', background=theme['buttonbg'], foreground=theme['buttonfg'], bordercolor=theme['buttonbg'])
        style.configure('TEntry', fieldbackground=theme['inputbg'], foreground=theme['inputfg'])
        style.configure('Treeview', background=theme['bg'], foreground=theme['fg'], fieldbackground=theme['bg'])
        style.configure('Treeview.Heading', background=theme['buttonbg'], foreground=theme['buttonfg'])
        style.map('Treeview',
                  background=[('selected', theme['selectbg'])],
                  foreground=[('selected', theme['selectfg'])])
        style.configure('TLabel', background=theme['framebg'], foreground=theme['fg'])
        style.configure('TRadiobutton', background=theme['framebg'], foreground=theme['fg'])
        style.configure('TCombobox', fieldbackground=theme['inputbg'], foreground=theme['inputfg'], background=theme['buttonbg'])
        self.details_text.configure(bg=theme['textbg'],
                                    fg=theme['textfg'],
                                    insertbackground=theme['fg'],
                                    selectbackground=theme['selectbg'],
                                    selectforeground=theme['selectfg'])
        for widget in self.root.winfo_children():
            if isinstance(widget, ttk.Frame) or isinstance(widget, ttk.LabelFrame):
                widget.configure(style='TFrame')
        menu_bg = theme['buttonbg']
        menu_fg = theme['buttonfg']
        self.menu_bar.configure(bg=menu_bg, fg=menu_fg)
        for menu in [self.file_menu, self.view_menu, self.settings_menu, self.theme_menu]:
            menu.configure(bg=menu_bg, fg=menu_fg,
                           activebackground=theme['selectbg'],
                           activeforeground=theme['selectfg'])

    def _load_file(self):
        filename = filedialog.askopenfilename(
            filetypes=[("Text files", "*.txt"), ("All files", "*.*")]
        )
        if not filename:
            return
        self.current_file = filename
        self.settings.clear()
        self.settings_list.delete(*self.settings_list.get_children())
        try:
            with open(filename, 'r', encoding='ansi') as f:
                self.original_lines = f.readlines()
            current_setting = None
            def finalize_setting(s: BIOSSetting):
                if s is not None:
                    if s.options is None:
                        s.options = []
                    if len(s.options) == 1 and s.active_option is None:
                        s.value = s.options[0]
                        s.options = []
                    self.settings.append(s)
            re_bracket_option = re.compile(r'^\**\[(.*?)\](.*)')
            for raw_line in self.original_lines:
                line = self.re_comment.sub('', raw_line).strip()
                if not line:
                    continue
                match_setup = self.re_setup_question.match(line)
                if match_setup:
                    finalize_setting(current_setting)
                    current_setting = BIOSSetting(
                        setup_question=match_setup.group(1).strip(),
                        options=[],
                        content=[]
                    )
                    continue
                if not current_setting:
                    continue
                match_help = self.re_help_string.match(line)
                if match_help:
                    current_setting.help_string = match_help.group(1).strip()
                    continue
                match_token = self.re_token.match(line)
                if match_token:
                    current_setting.token = match_token.group(1).strip()
                    continue
                match_off = self.re_offset.match(line)
                if match_off:
                    current_setting.offset = match_off.group(1).strip()
                    continue
                match_wid = self.re_width.match(line)
                if match_wid:
                    current_setting.width = match_wid.group(1).strip()
                    continue
                match_def = self.re_bios_default.match(line)
                if match_def:
                    current_setting.bios_default = match_def.group(1).strip()
                    continue
                match_opt = self.re_options.match(line)
                if match_opt:
                    remainder = match_opt.group(1).strip()
                    self._parse_options_line(remainder, current_setting, re_bracket_option)
                    continue
                match_val = self.re_value.match(line)
                if match_val:
                    val = match_val.group(1).strip()
                    current_setting.value = val
                    continue
                bracket_line = re_bracket_option.match(line)
                if bracket_line:
                    self._parse_options_line(line, current_setting, re_bracket_option)
                    continue
                current_setting.content.append(line)
            finalize_setting(current_setting)
            self._populate_settings_list()
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load file: {str(e)}")

    def _parse_options_line(self, line: str, setting: BIOSSetting, bracket_regex: re.Pattern):
        pattern = re.compile(r'(\*?)\[([^\]]+)\](\S.*?|)$')
        found = pattern.findall(line)
        if not found:
            star_in_front = line.strip().startswith('*')
            clean_line = line.lstrip('*').strip()
            if clean_line:
                index = len(setting.options)
                setting.options.append(clean_line)
                if star_in_front:
                    setting.active_option = index
            return
        for match in found:
            star, bracket_num, remainder = match
            option_str = f"[{bracket_num}]{remainder}".strip()
            index = len(setting.options)
            setting.options.append(option_str)
            if star == '*':
                setting.active_option = index

    def _populate_settings_list(self, filter_text: str = ''):
        self.settings_list.delete(*self.settings_list.get_children())
        for setting in self.settings:
            if filter_text.lower() in setting.setup_question.lower():
                display_value = ""
                if setting.options:
                    if setting.active_option is not None and 0 <= setting.active_option < len(setting.options):
                        display_value = setting.options[setting.active_option]
                    else:
                        display_value = ", ".join(setting.options)
                elif setting.value is not None:
                    display_value = setting.value
                self.settings_list.insert('', 'end', 
                                          iid=setting.unique_id,
                                          text=setting.setup_question, 
                                          values=(display_value,))

    def _filter_settings(self, *args):
        self._populate_settings_list(self.search_var.get())

    def _on_setting_select(self, event):
        selection = self.settings_list.selection()
        if not selection:
            return
        unique_id = selection[0]
        setting = next((s for s in self.settings if s.unique_id == unique_id), None)
        if not setting:
            return
        for widget in self.options_frame.winfo_children():
            widget.destroy()
        self.details_text.config(state=tk.NORMAL)
        self.details_text.delete('1.0', tk.END)
        details_lines = [
            f"Setup Question: {setting.setup_question}",
            f"Help String: {setting.help_string}",
            f"Token: {setting.token}",
            f"Offset: {setting.offset}",
            f"Width: {setting.width}"
        ]
        if setting.bios_default is not None:
            details_lines.append(f"BIOS Default: {setting.bios_default}")
        if setting.value:
            details_lines.append(f"Value: {setting.value}")
        final_details = "\n".join(details_lines) + "\n"
        self.details_text.insert('1.0', final_details)
        self.details_text.config(state=tk.DISABLED)
        if setting.options:
            var = tk.StringVar(value="")
            for i, option in enumerate(setting.options):
                rb = ttk.Radiobutton(
                    self.options_frame,
                    text=option,
                    value=option,
                    variable=var,
                    command=lambda s=setting, idx=i: self._update_option(s, idx)
                )
                rb.pack(anchor=tk.W)
            if setting.active_option is not None and 0 <= setting.active_option < len(setting.options):
                var.set(setting.options[setting.active_option])
        elif setting.value is not None:
            var = tk.StringVar(value=setting.value)
            entry = ttk.Entry(self.options_frame, textvariable=var)
            entry.pack(fill=tk.X, padx=5, pady=5)
            update_btn = ttk.Button(self.options_frame, text="Update Value",
                                    command=lambda s=setting, v=var: self._update_value(s, v))
            update_btn.pack()

    def _update_option(self, setting: BIOSSetting, new_active: int):
        setting.active_option = new_active
        self._populate_settings_list(self.search_var.get())

    def _update_value(self, setting: BIOSSetting, value_var: tk.StringVar):
        setting.value = value_var.get()
        self._populate_settings_list(self.search_var.get())

    def _save_file(self):
        if not self.current_file or not self.original_lines:
            messagebox.showwarning("Warning", "No file loaded")
            return
        save_path = filedialog.asksaveasfilename(
            defaultextension=".txt",
            filetypes=[("Text files", "*.txt"), ("All files", "*.*")]
        )
        if not save_path:
            return
        try:
            new_lines = self.original_lines[:]
            qmap = {
                (s.setup_question.strip(), s.token.strip(), s.offset.strip()): s
                for s in self.settings
                if s.setup_question and s.token and s.offset
            }
            re_setup = re.compile(r'^Setup\s+Question\s*=\s*(.*)', re.IGNORECASE)
            re_token = re.compile(r'^Token\s*=\s*(.*)', re.IGNORECASE)
            re_offset = re.compile(r'^Offset\s*=\s*(.*)', re.IGNORECASE)
            re_options_line = re.compile(r'^Options\s*=', re.IGNORECASE)
            re_value_line = re.compile(r'^Value\s*=', re.IGNORECASE)
            re_bracket_line = re.compile(r'^\s*\*?\[.*?\]')
            current_setting = None
            current_sq = None
            current_token = None
            current_offset = None
            skip_lines_until = -1
            i = 0
            while i < len(new_lines):
                if i <= skip_lines_until:
                    i += 1
                    continue
                raw_line = new_lines[i]
                line_stripped = self.re_comment.sub('', raw_line).strip()
                if not line_stripped:
                    i += 1
                    continue
                match_sq = re_setup.match(line_stripped)
                if match_sq:
                    current_sq = match_sq.group(1).strip()
                    current_token = None
                    current_offset = None
                    current_setting = None
                    i += 1
                    continue
                match_tk = re_token.match(line_stripped)
                if match_tk:
                    current_token = match_tk.group(1).strip()
                    i += 1
                    continue
                match_off = re_offset.match(line_stripped)
                if match_off:
                    current_offset = match_off.group(1).strip()
                    if current_sq and current_token and current_offset:
                        current_setting = qmap.get((current_sq, current_token, current_offset))
                    i += 1
                    continue
                if current_setting is None:
                    i += 1
                    continue
                if re_options_line.match(line_stripped):
                    option_block_end = i + 1
                    while option_block_end < len(new_lines):
                        next_line = self.re_comment.sub('', new_lines[option_block_end]).strip()
                        if not re_bracket_line.match(next_line):
                            break
                        option_block_end += 1
                    if current_setting.options:
                        new_block = []
                        for idx, opt in enumerate(current_setting.options):
                            prefix = "Options\t=" if idx == 0 else "         "
                            is_active = (current_setting.active_option == idx)
                            original_line = new_lines[i].strip()
                            comment_match = re.search(r'(//.*)$', original_line)
                            comment = f"\t{comment_match.group(1)}" if idx == 0 and comment_match else ""
                            line = f"{prefix}{'*' if is_active else ''}{opt}{comment}\n"
                            new_block.append(line)
                        new_lines[i:option_block_end] = new_block
                        skip_lines_until = i + len(new_block) - 1
                    i = option_block_end
                    continue
                if re_value_line.match(line_stripped):
                    if current_setting.value is not None:
                        comment_match = re.search(r'(//.*)$', raw_line)
                        comment = f"{comment_match.group(1)}" if comment_match else ""
                        leading_whitespace = re.match(r'^\s*', raw_line).group(0)
                        new_lines[i] = (
                            f"{leading_whitespace}Value\t={current_setting.value}"
                            f"{f'\t{comment}' if comment else ''}\n"
                        )
                    i += 1
                    continue
                i += 1
            with open(save_path, 'w', encoding='ansi') as f:
                f.writelines(new_lines)
            messagebox.showinfo("Success", f"File saved successfully to {save_path}")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save file: {str(e)}")

    def run(self):
        self.root.mainloop()

if __name__ == "__main__":
    app = BIOSSettingsManager()
    app.run()
