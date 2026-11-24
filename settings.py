#!/usr/bin/env python3
#encoding=utf-8

try:
    # for Python2
    from Tkinter import *
    import ttk
    import tkMessageBox as messagebox
except ImportError:
    # for Python3
    from tkinter import *
    from tkinter import ttk
    from tkinter import messagebox

import os
import sys

if getattr(sys, "frozen", False):
    if sys.stdout is None:
        sys.stdout = open(os.devnull, "w")
    if sys.stderr is None:
        sys.stderr = open(os.devnull, "w")
import json
import platform
import shutil
import socket
import subprocess

DEFAULT_DEBUG_ADDRESS = "127.0.0.1:9222"
DEFAULT_CHROME_PROFILE_DIRNAME = "tixcraft-chrome-profile"

CONST_APP_VERSION = u"MaxBot (2019.09.24-py3-sel4)"

CONST_FROM_TOP_TO_BOTTOM = u"from top to bottom"
CONST_FROM_BOTTOM_TO_TOP = u"from bottom to top"
CONST_RANDOM = u"random"
CONST_SELECT_ORDER_DEFAULT = CONST_FROM_TOP_TO_BOTTOM
CONST_SELECT_OPTIONS_DEFAULT = (CONST_FROM_TOP_TO_BOTTOM, CONST_FROM_BOTTOM_TO_TOP, CONST_RANDOM)
CONST_SELECT_OPTIONS_ARRAY = [CONST_FROM_TOP_TO_BOTTOM, CONST_FROM_BOTTOM_TO_TOP, CONST_RANDOM]

config_filepath = None
config_dict = None

window = None

btn_save = None
btn_exit = None


def get_app_root():
    if hasattr(sys, 'frozen'):
        basis = sys.executable
    else:
        basis = os.path.abspath(__file__)
    return os.path.dirname(basis)


def get_default_config():
    return {
        "homepage": "https://tixcraft.com",
        "browser": "chrome",
        "browser_debug_address": "",
        "ticket_number": 2,
        "facebook_account": "",
        "tixcraft": {
            "date_auto_select": {
                "enable": True,
                "mode": CONST_SELECT_ORDER_DEFAULT,
                "date_keyword": "",
            },
            "area_auto_select": {
                "enable": True,
                "mode": CONST_RANDOM,
                "area_keyword": "",
            },
            "captcha_assist": False,
            "captcha_auto_ocr": False,
            "auto_press_confirm_button": False,
            "captcha_prompt_timeout_s": 60,
            "captcha_max_retries": 3,
        },
        "kktix": {
            "auto_press_next_step_button": True,
            "auto_fill_ticket_number": True,
            "auto_fill_ticket_price": "$1,500",
            "area_mode": CONST_RANDOM,
            "area_keyword": "",
            "area_exclude_keyword": "",
            "answer_dictionary": "",
        },
    }


def load_json(filepath=None):
    # 讀取檔案裡的參數值
    app_root = get_app_root()

    global config_filepath
    config_filepath = filepath if filepath is not None else os.path.join(app_root, 'settings.json')

    global config_dict
    config_dict = None
    if os.path.isfile(config_filepath):
        with open(config_filepath, encoding='utf-8') as json_data:
            config_dict = json.load(json_data)
    else:
        config_dict = get_default_config()
    return config_dict


def btn_save_clicked():
    btn_save_act()


def btn_save_act(slience_mode=False):

    is_all_data_correct = True

    global config_filepath

    global config_dict
    if config_dict is not None:
        # read user input

        global combo_homepage
        global combo_browser
        global txt_ticket_number
        global txt_browser_debug_address
        #global txt_facebook_account

        global chk_state_auto_press_next_step_button
        global chk_state_auto_fill_ticket_number
        global combo_kktix_area_mode
        global txt_kktix_area_keyword
        global txt_kktix_area_exclude_keyword
        global txt_kktix_answer_dictionary

        global chk_state_date_auto_select
        global txt_date_keyword
        global chk_state_area_auto_select
        global txt_area_keyword
        global chk_state_captcha_assist
        global chk_state_captcha_auto_ocr
        global chk_state_auto_press_confirm_button
        global txt_captcha_prompt_timeout_s
        global txt_captcha_max_retries

        global combo_date_auto_select_mode
        global combo_area_auto_select_mode

        if is_all_data_correct:
            if combo_homepage.get().strip() == "":
                is_all_data_correct = False
                messagebox.showerror("Error", "Please enter homepage")
            else:
                config_dict["homepage"] = combo_homepage.get().strip()

        if is_all_data_correct:
            if combo_browser.get().strip() == "":
                is_all_data_correct = False
                messagebox.showerror("Error", "Please enter browser: chrome or firefox")
            else:
                config_dict["browser"] = combo_browser.get().strip()

        if is_all_data_correct:
            config_dict["browser_debug_address"] = txt_browser_debug_address.get().strip()

        if is_all_data_correct:
            ticket_num_str = txt_ticket_number.get().strip()
            if ticket_num_str == "":
                is_all_data_correct = False
                messagebox.showerror("Error", "Please enter ticket number")
            else:
                try:
                    parsed_ticket_number = int(ticket_num_str)
                    if parsed_ticket_number <= 0:
                        raise ValueError("ticket_number must be positive")
                    config_dict["ticket_number"] = parsed_ticket_number
                except ValueError:
                    is_all_data_correct = False
                    messagebox.showerror("Error", "Ticket number must be a positive integer")

        if is_all_data_correct:
            #config_dict["facebook_account"] = txt_facebook_account.get().strip()
            pass

        if is_all_data_correct:
            config_dict.setdefault("kktix", {})
            config_dict["kktix"]["auto_press_next_step_button"] = bool(chk_state_auto_press_next_step_button.get())
            config_dict["kktix"]["auto_fill_ticket_number"] = bool(chk_state_auto_fill_ticket_number.get())
            config_dict["kktix"]["area_mode"] = combo_kktix_area_mode.get().strip()
            config_dict["kktix"]["area_keyword"] = txt_kktix_area_keyword.get().strip()
            config_dict["kktix"]["area_exclude_keyword"] = txt_kktix_area_exclude_keyword.get().strip()
            config_dict["kktix"]["answer_dictionary"] = txt_kktix_answer_dictionary.get().strip()

            config_dict.setdefault("tixcraft", {})
            config_dict["tixcraft"].setdefault("date_auto_select", {})
            config_dict["tixcraft"].setdefault("area_auto_select", {})

            config_dict["tixcraft"]["date_auto_select"]["enable"] = bool(chk_state_date_auto_select.get())
            config_dict["tixcraft"]["date_auto_select"]["date_keyword"] = txt_date_keyword.get().strip()

            config_dict["tixcraft"]["area_auto_select"]["enable"] = bool(chk_state_area_auto_select.get())
            config_dict["tixcraft"]["area_auto_select"]["area_keyword"] = txt_area_keyword.get().strip()

            config_dict["tixcraft"]["date_auto_select"]["mode"] = combo_date_auto_select_mode.get().strip()
            config_dict["tixcraft"]["area_auto_select"]["mode"] = combo_area_auto_select_mode.get().strip()

            try:
                prompt_timeout_s = int(txt_captcha_prompt_timeout_s.get().strip())
                max_retries = int(txt_captcha_max_retries.get().strip())
                if prompt_timeout_s <= 0 or max_retries <= 0:
                    raise ValueError("CAPTCHA values must be positive")
                config_dict["tixcraft"]["captcha_assist"] = bool(chk_state_captcha_assist.get())
                config_dict["tixcraft"]["captcha_auto_ocr"] = bool(chk_state_captcha_auto_ocr.get())
                config_dict["tixcraft"]["auto_press_confirm_button"] = bool(chk_state_auto_press_confirm_button.get())
                config_dict["tixcraft"]["captcha_prompt_timeout_s"] = prompt_timeout_s
                config_dict["tixcraft"]["captcha_max_retries"] = max_retries
            except ValueError:
                is_all_data_correct = False
                messagebox.showerror("Error", "CAPTCHA timeout and retries must be positive integers")

        # save config.
        if is_all_data_correct:
            with open(config_filepath, 'w', encoding='utf-8') as outfile:
                json.dump(config_dict, outfile, indent=2, ensure_ascii=False)

            if slience_mode == False:
                messagebox.showinfo("File Save", "Done ^_^")

    return is_all_data_correct


def get_pause_file_path():
    return os.path.join(get_app_root(), '.bot_paused')


def is_bot_paused(pause_file=None):
    path = pause_file if pause_file is not None else get_pause_file_path()
    return os.path.isfile(path)


def set_bot_paused(paused, pause_file=None):
    path = pause_file if pause_file is not None else get_pause_file_path()
    if paused:
        with open(path, 'w', encoding='utf-8') as f:
            f.write('paused\n')
        return True
    if os.path.isfile(path):
        try:
            os.remove(path)
        except OSError:
            pass
    return False


def toggle_bot_paused(pause_file=None):
    return set_bot_paused(not is_bot_paused(pause_file), pause_file)


def update_pause_ui(paused=None):
    if paused is None:
        paused = is_bot_paused()
    if 'btn_pause' in globals() and btn_pause is not None:
        btn_pause.config(text="Resume" if paused else "Pause")
    if 'lbl_bot_status' in globals() and lbl_bot_status is not None:
        lbl_bot_status.config(
            text="Status: Paused (manual control)" if paused else "Status: Running"
        )


def parse_debug_address(addr):
    text = (addr or "").strip()
    if ":" in text:
        host, port_str = text.rsplit(":", 1)
        host = host.strip() or "127.0.0.1"
        try:
            port = int(port_str.strip())
            if 1 <= port <= 65535:
                return host, port
        except ValueError:
            pass
    return "127.0.0.1", 9222


def is_debug_port_open(addr=DEFAULT_DEBUG_ADDRESS, timeout=0.25):
    host, port = parse_debug_address(addr)
    try:
        conn = socket.create_connection((host, port), timeout=timeout)
        conn.close()
        return True
    except OSError:
        return False


def find_chrome_executable(system_name=None):
    sys_name = system_name or platform.system()
    candidates = []
    if sys_name == "Windows":
        for env_key in ("ProgramFiles", "ProgramFiles(x86)", "LOCALAPPDATA"):
            base = os.environ.get(env_key)
            if base:
                candidates.append(os.path.join(base, "Google", "Chrome", "Application", "chrome.exe"))
        for cmd in ("chrome.exe", "chrome"):
            found = shutil.which(cmd)
            if found:
                candidates.append(found)
    elif sys_name == "Darwin":
        candidates.extend([
            "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
            os.path.expanduser("~/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"),
        ])
        for cmd in ("Google Chrome", "google-chrome"):
            found = shutil.which(cmd)
            if found:
                candidates.append(found)
    else:
        for cmd in ("google-chrome", "google-chrome-stable", "chromium", "chromium-browser"):
            found = shutil.which(cmd)
            if found:
                candidates.append(found)

    for path in candidates:
        if path and os.path.isfile(path):
            return path
    return None


def launch_debug_chrome(target_url, debug_address=DEFAULT_DEBUG_ADDRESS, profile_dir=None):
    chrome_bin = find_chrome_executable()
    if not chrome_bin:
        raise FileNotFoundError("Google Chrome executable not found.")
    _, port = parse_debug_address(debug_address)
    user_data_dir = profile_dir or os.path.join(os.path.expanduser("~"), DEFAULT_CHROME_PROFILE_DIRNAME)
    url = (target_url or "").strip() or "https://tixcraft.com"
    return subprocess.Popen([
        chrome_bin,
        "--remote-debugging-port=%d" % port,
        "--user-data-dir=%s" % user_data_dir,
        url,
    ])


def btn_clear_debug_address_clicked():
    if 'txt_browser_debug_address_value' in globals() and txt_browser_debug_address_value is not None:
        txt_browser_debug_address_value.set("")


def btn_open_browser_clicked():
    set_bot_paused(True)
    update_pause_ui(True)

    if 'combo_browser' in globals() and combo_browser is not None:
        combo_browser.set("chrome")

    addr = DEFAULT_DEBUG_ADDRESS
    if 'txt_browser_debug_address' in globals() and txt_browser_debug_address is not None:
        current = txt_browser_debug_address.get().strip()
        addr = current if current else DEFAULT_DEBUG_ADDRESS
    if 'txt_browser_debug_address_value' in globals() and txt_browser_debug_address_value is not None:
        txt_browser_debug_address_value.set(addr)

    btn_save_act(slience_mode=True)

    target_url = "https://tixcraft.com"
    if 'combo_homepage' in globals() and combo_homepage is not None:
        selected = combo_homepage.get().strip()
        if selected:
            target_url = selected

    try:
        launch_debug_chrome(target_url, debug_address=addr)
    except Exception as exc:
        messagebox.showerror("Open Browser Error", str(exc))


def btn_pause_clicked():
    paused = toggle_bot_paused()
    update_pause_ui(paused)


def btn_run_clicked():
    if btn_save_act(slience_mode=True):
        set_bot_paused(False)
        update_pause_ui(False)
        app_root = get_app_root()
        if hasattr(sys, 'frozen'):
            # check platform here.
            if platform.system() == 'Windows':
                subprocess.Popen([os.path.join(app_root, "chrome_tixcraft.exe")], cwd=app_root)
            else:
                subprocess.Popen([os.path.join(app_root, "chrome_tixcraft")], cwd=app_root)
        else:
            script_path = os.path.join(app_root, "chrome_tixcraft.py")
            subprocess.Popen([sys.executable, script_path], cwd=app_root)


def btn_exit_clicked():
    set_bot_paused(False)
    root.destroy()


def resize_root_to_fit():
    if 'root' in globals() and root is not None:
        root.update_idletasks()
        min_width = max(500, root.winfo_reqwidth() + 24)
        min_height = max(540, root.winfo_reqheight() + 24)
        root.minsize(min_width, min_height)
        root.geometry("%dx%d" % (min_width, min_height))


def callbackHomepageOnChange(event):
    if 'txt_browser_debug_address_value' in globals() and txt_browser_debug_address_value is not None:
        txt_browser_debug_address_value.set("")
    showHideBlocks()

def callbackDateAutoOnChange():
    showHideTixcraftBlocks()
    resize_root_to_fit()

def showHideBlocks(all_layout_visible=False):
    global UI_PADDING_X

    global frame_group_kktix
    global frame_group_kktix_index
    global frame_group_tixcraft
    global frame_group_tixcraft_index

    # for kktix only.
    global lbl_kktix_area_mode
    global lbl_kktix_answer_dictionary

    global txt_kktix_answer_dictionary
    global txt_kktix_answer_dictionary_index

    global combo_kktix_area_mode
    global combo_kktix_area_mode_index

    new_homepage = combo_homepage.get().strip()
    #print("new homepage value:", new_homepage)

    show_block_index = 0
    if u'tixcraft' in new_homepage:
        show_block_index = 1
    if u'famiticket' in new_homepage:
        show_block_index = 1

    # all_layout_visible==true, means enter function when onload().
    #print("all_layout_visible:", all_layout_visible)
    if all_layout_visible:
        if show_block_index==0:
            frame_group_tixcraft.grid_forget()

            if u'kktix' in new_homepage:
                #combo_kktix_area_mode.grid(column=1, row=combo_kktix_area_mode_index, sticky = W)
                #txt_kktix_answer_dictionary.grid(column=1, row=txt_kktix_answer_dictionary_index, sticky = W)
                pass
            else:
                combo_kktix_area_mode.grid_forget()
                txt_kktix_answer_dictionary.grid_forget()

        else:
            frame_group_kktix.grid_forget()
    else:
        if show_block_index == 0:
            frame_group_kktix.grid(column=0, row=frame_group_kktix_index, padx=UI_PADDING_X)
            frame_group_tixcraft.grid_forget()

            if u'kktix' in new_homepage:
                combo_kktix_area_mode.grid(column=1, row=combo_kktix_area_mode_index, sticky = W)
                txt_kktix_answer_dictionary.grid(column=1, row=txt_kktix_answer_dictionary_index, sticky = W)
            else:
                combo_kktix_area_mode.grid_forget()
                txt_kktix_answer_dictionary.grid_forget()

        else:
            frame_group_tixcraft.grid(column=0, row=frame_group_tixcraft_index, padx=UI_PADDING_X)
            frame_group_kktix.grid_forget()

    lbl_kktix_area_mode_default = 'Area select order'
    lbl_kktix_answer_default = 'Answer Dictionary'
    if u'kktix' in new_homepage:
        lbl_kktix_area_mode['text'] = lbl_kktix_area_mode_default
        lbl_kktix_answer_dictionary['text'] = lbl_kktix_answer_default
    else:
        lbl_kktix_area_mode['text'] = ''
        lbl_kktix_answer_dictionary['text'] = ''

    if 'btn_open_browser' in globals() and btn_open_browser is not None:
        if u'kktix' in new_homepage or u'tixcraft' in new_homepage:
            btn_open_browser.grid(column=1, row=0)
        else:
            btn_open_browser.grid_remove()

    showHideTixcraftBlocks()
    if not all_layout_visible:
        resize_root_to_fit()


def showHideTixcraftBlocks():
    # for tixcraft show/hide enable.
    # field 1
    global chk_state_date_auto_select

    global date_auto_select_mode_index
    global lbl_date_auto_select_mode
    global combo_date_auto_select_mode

    global date_keyword_index
    global lbl_date_keyword
    global txt_date_keyword

    # field 2
    global chk_state_area_auto_select
    global chk_area_auto_select

    global area_auto_select_index
    global lbl_area_auto_select_mode
    global combo_area_auto_select_mode

    global area_keyword_index
    global lbl_area_keyword
    global txt_area_keyword

    new_date_enable = bool(chk_state_date_auto_select.get())
    new_area_enable = bool(chk_state_area_auto_select.get())
    #print("new new_date_enable value:", new_date_enable)
    #print("new new_area_enable value:", new_area_enable)

    if new_date_enable:
        # show
        lbl_date_auto_select_mode.grid(column=0, row=date_auto_select_mode_index, sticky = E)
        combo_date_auto_select_mode.grid(column=1, row=date_auto_select_mode_index, sticky = W)

        lbl_date_keyword.grid(column=0, row=date_keyword_index, sticky = E)
        txt_date_keyword.grid(column=1, row=date_keyword_index, sticky = W)
    else:
        # hide
        lbl_date_auto_select_mode.grid_forget()
        combo_date_auto_select_mode.grid_forget()

        lbl_date_keyword.grid_forget()
        txt_date_keyword.grid_forget()

    if new_area_enable:
        # show
        lbl_area_auto_select_mode.grid(column=0, row=area_auto_select_index, sticky = E)
        combo_area_auto_select_mode.grid(column=1, row=area_auto_select_index, sticky = W)

        lbl_area_keyword.grid(column=0, row=area_keyword_index, sticky = E)
        txt_area_keyword.grid(column=1, row=area_keyword_index, sticky = W)
    else:
        # hide
        lbl_area_auto_select_mode.grid_forget()
        combo_area_auto_select_mode.grid_forget()

        lbl_area_keyword.grid_forget()
        txt_area_keyword.grid_forget()


def MainMenu(root):
    global UI_PADDING_X
    UI_PADDING_X = 15
    global UI_PADDING_Y
    UI_PADDING_Y = 10

    lbl_homepage = None
    lbl_browser = None
    lbl_ticket_number = None
    lbl_kktix = None
    lbl_tixcraft = None

    homepage = None
    browser = None
    browser_debug_address = ""
    ticket_number = 1

    auto_press_next_step_button = None
    auto_fill_ticket_number = None

    kktix_area_mode = ""
    kktix_area_keyword = ""
    kktix_area_exclude_keyword = ""
    kktix_answer_dictionary = ""

    date_auto_select_enable = None
    date_auto_select_mode = ""
    date_keyword = ""

    area_auto_select_enable = None
    area_auto_select_mode = ""
    area_keyword = ""

    captcha_assist = False
    captcha_auto_ocr = False
    auto_press_confirm_button = False
    captcha_prompt_timeout_s = 60
    captcha_max_retries = 3

    global config_dict
    if not config_dict is None:
        # read config.
        if u'homepage' in config_dict:
            homepage = config_dict["homepage"]

        if u'browser' in config_dict:
            browser = config_dict["browser"]

        browser_debug_address = ""
        if 'browser_debug_address' in config_dict:
            saved_debug_addr = str(config_dict["browser_debug_address"] or "").strip()
            if saved_debug_addr and is_debug_port_open(saved_debug_addr):
                browser_debug_address = saved_debug_addr

        # default ticket number
        # 說明：自動選擇的票數
        ticket_number = "2"
        if u'ticket_number' in config_dict:
            ticket_number = str(config_dict["ticket_number"])

        facebook_account = ""
        if 'facebook_account' in config_dict:
            facebook_account = str(config_dict["facebook_account"])

        # for ["kktix"]
        if 'kktix' in config_dict:
            auto_press_next_step_button = config_dict["kktix"]["auto_press_next_step_button"]
            auto_fill_ticket_number = config_dict["kktix"]["auto_fill_ticket_number"]

            if 'area_mode' in config_dict["kktix"]:
                kktix_area_mode = config_dict["kktix"]["area_mode"]
                kktix_area_mode = kktix_area_mode.strip()
            if not kktix_area_mode in CONST_SELECT_OPTIONS_ARRAY:
                kktix_area_mode = CONST_SELECT_ORDER_DEFAULT

            if 'area_keyword' in config_dict["kktix"]:
                kktix_area_keyword = config_dict["kktix"]["area_keyword"]
                if kktix_area_keyword is None:
                    kktix_area_keyword = ""
                kktix_area_keyword = kktix_area_keyword.strip()

            if 'area_exclude_keyword' in config_dict["kktix"]:
                kktix_area_exclude_keyword = config_dict["kktix"]["area_exclude_keyword"]
                if kktix_area_exclude_keyword is None:
                    kktix_area_exclude_keyword = ""
                kktix_area_exclude_keyword = kktix_area_exclude_keyword.strip()

            if 'answer_dictionary' in config_dict["kktix"]:
                kktix_answer_dictionary = config_dict["kktix"]["answer_dictionary"]
                if kktix_answer_dictionary is None:
                    kktix_answer_dictionary = ""
                kktix_answer_dictionary = kktix_answer_dictionary.strip()

        # for ["tixcraft"]
        if 'tixcraft' in config_dict:
            date_auto_select_enable = config_dict["tixcraft"]["date_auto_select"]["enable"]
            date_auto_select_mode = config_dict["tixcraft"]["date_auto_select"]["mode"]

            if not date_auto_select_mode in CONST_SELECT_OPTIONS_ARRAY:
                date_auto_select_mode = CONST_SELECT_ORDER_DEFAULT

            if 'date_keyword' in config_dict["tixcraft"]["date_auto_select"]:
                date_keyword = config_dict["tixcraft"]["date_auto_select"]["date_keyword"]
                date_keyword = date_keyword.strip()

            area_auto_select_enable = config_dict["tixcraft"]["area_auto_select"]["enable"]
            area_auto_select_mode = config_dict["tixcraft"]["area_auto_select"]["mode"]

            if not area_auto_select_mode in CONST_SELECT_OPTIONS_ARRAY:
                area_auto_select_mode = CONST_SELECT_ORDER_DEFAULT

            if 'area_keyword' in config_dict["tixcraft"]["area_auto_select"]:
                area_keyword = config_dict["tixcraft"]["area_auto_select"]["area_keyword"]
                area_keyword = area_keyword.strip()

            captcha_assist = bool(config_dict["tixcraft"].get("captcha_assist", False))
            captcha_auto_ocr = bool(config_dict["tixcraft"].get("captcha_auto_ocr", False))
            auto_press_confirm_button = bool(config_dict["tixcraft"].get("auto_press_confirm_button", False))
            captcha_prompt_timeout_s = config_dict["tixcraft"].get("captcha_prompt_timeout_s", 60)
            captcha_max_retries = config_dict["tixcraft"].get("captcha_max_retries", 3)

        # output config:
        print("homepage", homepage)
        print("browser", browser)
        print("ticket_number", ticket_number)
        print("facebook_account", facebook_account)

        # for kktix
        print("==[kktix]==")
        print("auto_press_next_step_button", auto_press_next_step_button)
        print("auto_fill_ticket_number", auto_fill_ticket_number)
        print("kktix_area_mode", kktix_area_mode)
        print("kktix_area_keyword", kktix_area_keyword)
        print("kktix_area_exclude_keyword", kktix_area_exclude_keyword)
        print("kktix_answer_dictionary", kktix_answer_dictionary)

        # for tixcraft
        print("==[tixcraft]==")
        print("date_auto_select_enable", date_auto_select_enable)
        print("date_auto_select_mode", date_auto_select_mode)
        print("date_keyword", date_keyword)
        
        print("area_auto_select_enable", area_auto_select_enable)
        print("area_auto_select_mode", area_auto_select_mode)
        print("area_keyword", area_keyword)
    else:
        print('config is none')

    row_count = 0

    frame_group_header = Frame(root)
    group_row_count = 0

    # first row need padding Y
    lbl_homepage = Label(frame_group_header, text="Homepage", pady = UI_PADDING_Y)
    lbl_homepage.grid(column=0, row=group_row_count, sticky = E)

    #global txt_homepage
    #txt_homepage = Entry(root, width=20, textvariable = StringVar(root, value=homepage))
    #txt_homepage.grid(column=1, row=row_count)

    global combo_homepage
    combo_homepage = ttk.Combobox(frame_group_header, state="readonly")
    combo_homepage['values']= ("https://kktix.com","https://tixcraft.com","https://www.famiticket.com.tw","http://www.urbtix.hk/","https://www.cityline.com/")
    combo_homepage.set(homepage)
    combo_homepage.bind("<<ComboboxSelected>>", callbackHomepageOnChange)
    combo_homepage.grid(column=1, row=group_row_count, sticky = W)

    group_row_count+=1

    lbl_browser = Label(frame_group_header, text="Browser")
    lbl_browser.grid(column=0, row=group_row_count, sticky = E)

    #global txt_browser
    #txt_browser = Entry(root, width=20, textvariable = StringVar(root, value=browser))
    #txt_browser.grid(column=1, row=group_row_count)

    global combo_browser
    combo_browser = ttk.Combobox(frame_group_header, state="readonly")
    combo_browser['values']= ("chrome","firefox")
    #combo_browser.current(0)
    combo_browser.set(browser)
    combo_browser.grid(column=1, row=group_row_count, sticky = W)

    group_row_count+=1

    lbl_browser_debug_address = Label(frame_group_header, text="Attach Chrome (debug addr)")
    lbl_browser_debug_address.grid(column=0, row=group_row_count, sticky = E)

    global txt_browser_debug_address
    global txt_browser_debug_address_value
    txt_browser_debug_address_value = StringVar(frame_group_header, value=browser_debug_address)
    txt_browser_debug_address = Entry(frame_group_header, width=24, textvariable = txt_browser_debug_address_value)
    txt_browser_debug_address.grid(column=1, row=group_row_count, sticky = W)

    btn_clear_debug = ttk.Button(frame_group_header, text="Clear", width=6, command=btn_clear_debug_address_clicked)
    btn_clear_debug.grid(column=2, row=group_row_count, sticky = W, padx=(4, 0))

    group_row_count+=1

    lbl_ticket_number = Label(frame_group_header, text="Ticket Number")
    lbl_ticket_number.grid(column=0, row=group_row_count, sticky = E)

    global txt_ticket_number
    global txt_ticket_number_value
    txt_ticket_number_value = StringVar(frame_group_header, value=ticket_number)
    txt_ticket_number = Entry(frame_group_header, width=20, textvariable = txt_ticket_number_value)
    txt_ticket_number.grid(column=1, row=group_row_count, sticky = W)

    frame_group_header.grid(column=0, row=row_count, sticky = W, padx=UI_PADDING_X)

    '''
    row_count+=1

    lbl_facebook_account = Label(root, text="Facebook Account")
    lbl_facebook_account.grid(column=0, row=row_count, sticky = E)

    global txt_facebook_account
    global txt_facebook_account_value
    txt_facebook_account_value = StringVar(root, value=facebook_account)
    txt_facebook_account = Entry(root, width=20, textvariable = txt_facebook_account_value)
    txt_facebook_account.grid(column=1, row=row_count, sticky = W)
    '''

    row_count+=1

    global frame_group_kktix
    frame_group_kktix = Frame(root)
    group_row_count = 0

    #lbl_kktix = Label(frame_group_kktix, text="[ KKTIX / URBTIX / Cityline]")
    lbl_kktix = Label(frame_group_kktix, text="")
    lbl_kktix.grid(column=0, row=group_row_count)

    group_row_count+=1

    lbl_auto_press_next_step_button = Label(frame_group_kktix, text="Auto Press Next Step Button")
    lbl_auto_press_next_step_button.grid(column=0, row=group_row_count, sticky = E)

    global chk_state_auto_press_next_step_button
    chk_state_auto_press_next_step_button = BooleanVar()
    chk_state_auto_press_next_step_button.set(auto_press_next_step_button)

    chk_auto_press_next_step_button = Checkbutton(frame_group_kktix, text='Enable', variable=chk_state_auto_press_next_step_button)
    chk_auto_press_next_step_button.grid(column=1, row=group_row_count, sticky = W)

    group_row_count+=1

    lbl_auto_fill_ticket_number = Label(frame_group_kktix, text="Auto Fill Ticket Number")
    lbl_auto_fill_ticket_number.grid(column=0, row=group_row_count, sticky = E)

    global chk_state_auto_fill_ticket_number
    chk_state_auto_fill_ticket_number = BooleanVar()
    chk_state_auto_fill_ticket_number.set(auto_fill_ticket_number)

    chk_auto_auto_fill_ticket_number = Checkbutton(frame_group_kktix, text='Enable', variable=chk_state_auto_fill_ticket_number)
    chk_auto_auto_fill_ticket_number.grid(column=1, row=group_row_count, sticky = W)


    group_row_count+=1

    global lbl_kktix_area_mode
    lbl_kktix_area_mode = Label(frame_group_kktix, text="Area select order")
    lbl_kktix_area_mode.grid(column=0, row=group_row_count, sticky = E)

    global combo_kktix_area_mode
    global combo_kktix_area_mode_index
    combo_kktix_area_mode_index = group_row_count
    combo_kktix_area_mode = ttk.Combobox(frame_group_kktix, state="readonly")
    combo_kktix_area_mode['values']= CONST_SELECT_OPTIONS_DEFAULT
    combo_kktix_area_mode.set(kktix_area_mode)
    combo_kktix_area_mode.grid(column=1, row=group_row_count, sticky = W)

    group_row_count+=1

    lbl_kktix_area_keyword = Label(frame_group_kktix, text="Area Keyword")
    lbl_kktix_area_keyword.grid(column=0, row=group_row_count, sticky = E)

    global txt_kktix_area_keyword
    global txt_kktix_area_keyword_value
    txt_kktix_area_keyword_value = StringVar(frame_group_kktix, value=kktix_area_keyword)
    txt_kktix_area_keyword = Entry(frame_group_kktix, width=20, textvariable = txt_kktix_area_keyword_value)
    txt_kktix_area_keyword.grid(column=1, row=group_row_count, sticky = W)

    group_row_count+=1

    lbl_kktix_area_exclude_keyword = Label(frame_group_kktix, text="Area Exclude Keyword")
    lbl_kktix_area_exclude_keyword.grid(column=0, row=group_row_count, sticky = E)

    global txt_kktix_area_exclude_keyword
    global txt_kktix_area_exclude_keyword_value
    txt_kktix_area_exclude_keyword_value = StringVar(frame_group_kktix, value=kktix_area_exclude_keyword)
    txt_kktix_area_exclude_keyword = Entry(frame_group_kktix, width=20, textvariable = txt_kktix_area_exclude_keyword_value)
    txt_kktix_area_exclude_keyword.grid(column=1, row=group_row_count, sticky = W)

    group_row_count+=1

    global lbl_kktix_answer_dictionary
    lbl_kktix_answer_dictionary = Label(frame_group_kktix, text="Answer Dictionary")
    lbl_kktix_answer_dictionary.grid(column=0, row=group_row_count, sticky = E)

    global txt_kktix_answer_dictionary
    global txt_kktix_answer_dictionary_index
    txt_kktix_answer_dictionary_index = group_row_count
    global txt_kktix_answer_dictionary_value
    txt_kktix_answer_dictionary_value = StringVar(frame_group_kktix, value=kktix_answer_dictionary)
    txt_kktix_answer_dictionary = Entry(frame_group_kktix, width=20, textvariable = txt_kktix_answer_dictionary_value)
    txt_kktix_answer_dictionary.grid(column=1, row=group_row_count, sticky = W)

    group_row_count+=1

    lbl_hr = Label(frame_group_kktix, text="")
    lbl_hr.grid(column=0, row=group_row_count)

    global frame_group_kktix_index
    frame_group_kktix_index = row_count
    frame_group_kktix.grid(column=0, row=row_count, sticky = W, padx=UI_PADDING_X)

    row_count+=1

    global frame_group_tixcraft
    frame_group_tixcraft = Frame(root)
    group_row_count = 0

    #lbl_tixcraft = Label(frame_group_tixcraft, text="[ tixCraft / FamiTicket]")
    lbl_tixcraft = Label(frame_group_tixcraft, text="")
    lbl_tixcraft.grid(column=0, row=group_row_count)

    group_row_count+=1

    lbl_date_auto_select = Label(frame_group_tixcraft, text="Date Auto Select")
    lbl_date_auto_select.grid(column=0, row=group_row_count, sticky = E)

    global chk_state_date_auto_select
    chk_state_date_auto_select = BooleanVar()
    chk_state_date_auto_select.set(date_auto_select_enable)

    chk_date_auto_select = Checkbutton(frame_group_tixcraft, text='Enable', variable=chk_state_date_auto_select, command=callbackDateAutoOnChange)
    chk_date_auto_select.grid(column=1, row=group_row_count, sticky = W)

    group_row_count+=1

    global date_auto_select_mode_index
    date_auto_select_mode_index = group_row_count

    global lbl_date_auto_select_mode
    lbl_date_auto_select_mode = Label(frame_group_tixcraft, text="Date select order")
    lbl_date_auto_select_mode.grid(column=0, row=date_auto_select_mode_index, sticky = E)

    global combo_date_auto_select_mode
    combo_date_auto_select_mode = ttk.Combobox(frame_group_tixcraft, state="readonly")
    combo_date_auto_select_mode['values']= (CONST_FROM_TOP_TO_BOTTOM, CONST_FROM_BOTTOM_TO_TOP)
    combo_date_auto_select_mode.set(date_auto_select_mode)
    combo_date_auto_select_mode.grid(column=1, row=date_auto_select_mode_index, sticky = W)

    group_row_count+=1

    global date_keyword_index
    date_keyword_index = group_row_count

    global lbl_date_keyword
    lbl_date_keyword = Label(frame_group_tixcraft, text="Date Keyword")
    lbl_date_keyword.grid(column=0, row=date_keyword_index, sticky = E)

    global txt_date_keyword
    global txt_date_keyword_value
    txt_date_keyword_value = StringVar(frame_group_tixcraft, value=date_keyword)
    txt_date_keyword = Entry(frame_group_tixcraft, width=20, textvariable = txt_date_keyword_value)
    txt_date_keyword.grid(column=1, row=date_keyword_index, sticky = W)

    group_row_count+=1

    lbl_area_auto_select = Label(frame_group_tixcraft, text="Area Auto Select")
    lbl_area_auto_select.grid(column=0, row=group_row_count, sticky = E)

    global chk_state_area_auto_select
    chk_state_area_auto_select = BooleanVar()
    chk_state_area_auto_select.set(area_auto_select_enable)

    global chk_area_auto_select
    chk_area_auto_select = Checkbutton(frame_group_tixcraft, text='Enable', variable=chk_state_area_auto_select, command=callbackDateAutoOnChange)
    chk_area_auto_select.grid(column=1, row=group_row_count, sticky = W)

    group_row_count+=1

    global area_auto_select_index
    area_auto_select_index = group_row_count

    global lbl_area_auto_select_mode
    lbl_area_auto_select_mode = Label(frame_group_tixcraft, text="Area select order")
    lbl_area_auto_select_mode.grid(column=0, row=area_auto_select_index, sticky = E)

    global combo_area_auto_select_mode
    combo_area_auto_select_mode = ttk.Combobox(frame_group_tixcraft, state="readonly")
    combo_area_auto_select_mode['values']= CONST_SELECT_OPTIONS_DEFAULT
    combo_area_auto_select_mode.set(area_auto_select_mode)
    combo_area_auto_select_mode.grid(column=1, row=area_auto_select_index, sticky = W)

    group_row_count+=1

    global area_keyword_index
    area_keyword_index = group_row_count

    global lbl_area_keyword
    lbl_area_keyword = Label(frame_group_tixcraft, text="Area Keyword")
    lbl_area_keyword.grid(column=0, row=area_keyword_index, sticky = E)

    global txt_area_keyword
    global txt_ares_keyword_value
    txt_ares_keyword_value = StringVar(frame_group_tixcraft, value=area_keyword)
    txt_area_keyword = Entry(frame_group_tixcraft, width=20, textvariable = txt_ares_keyword_value)
    txt_area_keyword.grid(column=1, row=area_keyword_index, sticky = W)

    group_row_count+=1

    lbl_captcha_assist = Label(frame_group_tixcraft, text="CAPTCHA Assist")
    lbl_captcha_assist.grid(column=0, row=group_row_count, sticky = E)

    global chk_state_captcha_assist
    chk_state_captcha_assist = BooleanVar()
    chk_state_captcha_assist.set(captcha_assist)
    chk_captcha_assist = Checkbutton(frame_group_tixcraft, text="Enable", variable=chk_state_captcha_assist)
    chk_captcha_assist.grid(column=1, row=group_row_count, sticky = W)

    group_row_count+=1

    lbl_captcha_auto_ocr = Label(frame_group_tixcraft, text="CAPTCHA Auto OCR")
    lbl_captcha_auto_ocr.grid(column=0, row=group_row_count, sticky = E)

    global chk_state_captcha_auto_ocr
    chk_state_captcha_auto_ocr = BooleanVar()
    chk_state_captcha_auto_ocr.set(captcha_auto_ocr)
    chk_captcha_auto_ocr = Checkbutton(frame_group_tixcraft, text="Enable", variable=chk_state_captcha_auto_ocr)
    chk_captcha_auto_ocr.grid(column=1, row=group_row_count, sticky = W)

    group_row_count+=1

    lbl_auto_press_confirm_button = Label(frame_group_tixcraft, text="Auto Press Confirm Button")
    lbl_auto_press_confirm_button.grid(column=0, row=group_row_count, sticky = E)

    global chk_state_auto_press_confirm_button
    chk_state_auto_press_confirm_button = BooleanVar()
    chk_state_auto_press_confirm_button.set(auto_press_confirm_button)
    chk_auto_press_confirm_button = Checkbutton(frame_group_tixcraft, text="Enable", variable=chk_state_auto_press_confirm_button)
    chk_auto_press_confirm_button.grid(column=1, row=group_row_count, sticky = W)

    group_row_count+=1

    lbl_captcha_prompt_timeout_s = Label(frame_group_tixcraft, text="CAPTCHA Timeout (seconds)")
    lbl_captcha_prompt_timeout_s.grid(column=0, row=group_row_count, sticky = E)

    global txt_captcha_prompt_timeout_s
    global txt_captcha_prompt_timeout_s_value
    txt_captcha_prompt_timeout_s_value = StringVar(frame_group_tixcraft, value=str(captcha_prompt_timeout_s))
    txt_captcha_prompt_timeout_s = Entry(frame_group_tixcraft, width=20, textvariable = txt_captcha_prompt_timeout_s_value)
    txt_captcha_prompt_timeout_s.grid(column=1, row=group_row_count, sticky = W)

    group_row_count+=1

    lbl_captcha_max_retries = Label(frame_group_tixcraft, text="CAPTCHA Max Retries")
    lbl_captcha_max_retries.grid(column=0, row=group_row_count, sticky = E)

    global txt_captcha_max_retries
    global txt_captcha_max_retries_value
    txt_captcha_max_retries_value = StringVar(frame_group_tixcraft, value=str(captcha_max_retries))
    txt_captcha_max_retries = Entry(frame_group_tixcraft, width=20, textvariable = txt_captcha_max_retries_value)
    txt_captcha_max_retries.grid(column=1, row=group_row_count, sticky = W)

    global frame_group_tixcraft_index
    frame_group_tixcraft_index = row_count
    frame_group_tixcraft.grid(column=0, row=row_count, sticky = W, padx=UI_PADDING_X)

    row_count+=1

    lbl_hr = Label(root, text="")
    lbl_hr.grid(column=0, row=row_count)

    row_count+=1

    frame_action = Frame(root)

    btn_run = ttk.Button(frame_action, text="Run", command=btn_run_clicked)
    btn_run.grid(column=0, row=0)

    global btn_open_browser
    btn_open_browser = ttk.Button(frame_action, text="Open Browser", command=btn_open_browser_clicked)
    btn_open_browser.grid(column=1, row=0)

    global btn_pause
    btn_pause = ttk.Button(frame_action, text="Pause", command=btn_pause_clicked)
    btn_pause.grid(column=2, row=0)

    btn_save = ttk.Button(frame_action, text="Save", command=btn_save_clicked)
    btn_save.grid(column=3, row=0)

    btn_exit = ttk.Button(frame_action, text="Exit", command=btn_exit_clicked)
    btn_exit.grid(column=4, row=0)

    frame_action.grid(column=0, row=row_count, sticky = W, padx=UI_PADDING_X)

    row_count+=1

    global lbl_bot_status
    lbl_bot_status = Label(root, text="Status: Running")
    lbl_bot_status.grid(column=0, row=row_count, sticky = W, padx=UI_PADDING_X, pady=4)

    update_pause_ui()
    showHideBlocks(all_layout_visible=True)


def main():
    load_json()

    global root
    root = Tk()
    root.title(CONST_APP_VERSION)

    #style = ttk.Style(root)
    #style.theme_use('aqua')

    #root.configure(background='lightgray')
    # style configuration
    #style = Style(root)
    #style.configure('TLabel', background='lightgray', foreground='black')
    #style.configure('TFrame', background='lightgray')

    GUI = MainMenu(root)

    root.update_idletasks()
    min_width = max(500, root.winfo_reqwidth() + 24)
    min_height = max(540, root.winfo_reqheight() + 24)
    root.minsize(min_width, min_height)
    root.geometry("%dx%d" % (min_width, min_height))
    root.mainloop()

if __name__ == "__main__":
    main()