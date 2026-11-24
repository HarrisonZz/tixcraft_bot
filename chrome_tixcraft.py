#!/usr/bin/env python3
#encoding=utf-8
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import Select
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.firefox.service import Service as FirefoxService

from captcha_assist import CaptchaAssist

# for close tab.
from selenium.common.exceptions import NoSuchWindowException
from selenium.common.exceptions import WebDriverException
# for alert
from selenium.common.exceptions import UnexpectedAlertPresentException
from selenium.common.exceptions import NoAlertPresentException
# for alert 2
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException

# for wait #1
import time

import os
import sys
import platform
import json
import random

import re
from datetime import datetime
from urllib.parse import urlparse, parse_qs

# for error output
import logging
logging.basicConfig()
logger = logging.getLogger('logger')


#執行方式：python chrome_tixcraft.py 或 python3 chrome_tixcraft.py
#附註1：沒有寫的很好，很多地方應該可以模組化。
#附註2：

CONST_APP_VERSION = u"MaxBot (2019.09.24-py3-sel4)"

CONST_FROM_TOP_TO_BOTTOM = u"from top to bottom"
CONST_FROM_BOTTOM_TO_TOP = u"from bottom to top"
CONST_RANDOM = u"random"
CONST_SELECT_ORDER_DEFAULT = CONST_FROM_TOP_TO_BOTTOM
CONST_SELECT_OPTIONS_DEFAULT = (CONST_FROM_TOP_TO_BOTTOM, CONST_FROM_BOTTOM_TO_TOP, CONST_RANDOM)
CONST_SELECT_OPTIONS_ARRAY = [CONST_FROM_TOP_TO_BOTTOM, CONST_FROM_BOTTOM_TO_TOP, CONST_RANDOM]

# initial webdriver
# 說明：初始化 webdriver
driver = None


def get_app_root():
    if hasattr(sys, 'frozen'):
        basis = sys.executable
    else:
        basis = os.path.abspath(__file__)
    return os.path.dirname(basis)


app_root = get_app_root()
config_filepath = os.path.join(app_root, 'settings.json')
config_dict = None

homepage = "https://tixcraft.com"
browser = "chrome"
# 說明：設定後會「附加(attach)」到已手動開啟、並開啟了 remote-debugging 的 Chrome，
#       而不是由程式另外啟動一個新的 Chrome。例："127.0.0.1:9222"。
#       留空則維持原本行為（由程式啟動 Chrome）。
browser_debug_address = ""
ticket_number = "2"
facebook_account = ""

auto_press_next_step_button = False
auto_fill_ticket_number = True
auto_fill_ticket_price = None

date_auto_select_enable = True
date_auto_select_mode = CONST_SELECT_ORDER_DEFAULT
date_keyword = ""

area_auto_select_enable = True
area_auto_select_mode = CONST_SELECT_ORDER_DEFAULT
area_keyword = ""

captcha_assist_enabled = False
captcha_auto_ocr_enabled = False
captcha_prompt_timeout_s = 60
captcha_max_retries = 3
auto_press_confirm_button_enabled = False

kktix_area_auto_select_mode = CONST_SELECT_ORDER_DEFAULT
kktix_area_keyword = ""
kktix_area_exclude_keyword = ""

kktix_answer_dictionary = ""
kktix_answer_dictionary_list = None


def load_config(filepath=None):
    global config_filepath, config_dict
    global homepage, browser, browser_debug_address, ticket_number, facebook_account
    global auto_press_next_step_button, auto_fill_ticket_number
    global date_auto_select_enable, date_auto_select_mode, date_keyword
    global area_auto_select_enable, area_auto_select_mode, area_keyword
    global captcha_assist_enabled, captcha_prompt_timeout_s, captcha_max_retries, captcha_auto_ocr_enabled
    global auto_press_confirm_button_enabled
    global kktix_area_auto_select_mode, kktix_area_keyword, kktix_area_exclude_keyword
    global kktix_answer_dictionary, kktix_answer_dictionary_list

    if filepath is not None:
        config_filepath = filepath
    else:
        config_filepath = os.path.join(get_app_root(), 'settings.json')

    config_dict = None
    if os.path.isfile(config_filepath):
        with open(config_filepath, encoding='utf-8') as json_data:
            config_dict = json.load(json_data)

    if config_dict is None:
        print("Config error! settings.json not found:", config_filepath)
        return None

    # read config.
    if 'homepage' in config_dict:
        homepage = config_dict["homepage"]
    if 'browser' in config_dict:
        browser = str(config_dict["browser"]).strip().lower()

    browser_debug_address = ""
    if 'browser_debug_address' in config_dict:
        browser_debug_address = str(config_dict["browser_debug_address"] or "").strip()

    # default ticket number
    # 說明：自動選擇的票數
    ticket_number = ""
    if 'ticket_number' in config_dict:
        ticket_number = str(config_dict["ticket_number"]).strip()

    facebook_account = ""
    if 'facebook_account' in config_dict:
        facebook_account = str(config_dict["facebook_account"])

    # for ["kktix"]
    kktix_answer_dictionary = ""
    kktix_answer_dictionary_list = None
    kktix_area_keyword = ""
    kktix_area_exclude_keyword = ""
    kktix_area_auto_select_mode = CONST_SELECT_ORDER_DEFAULT
    if 'kktix' in config_dict:
        auto_press_next_step_button = bool(config_dict["kktix"].get("auto_press_next_step_button", False))
        auto_fill_ticket_number = bool(config_dict["kktix"].get("auto_fill_ticket_number", True))

        if 'area_mode' in config_dict["kktix"] and config_dict["kktix"]["area_mode"] is not None:
            kktix_area_auto_select_mode = str(config_dict["kktix"]["area_mode"]).strip()
        if kktix_area_auto_select_mode not in CONST_SELECT_OPTIONS_ARRAY:
            kktix_area_auto_select_mode = CONST_SELECT_ORDER_DEFAULT

        if 'area_keyword' in config_dict["kktix"]:
            kktix_area_keyword = config_dict["kktix"]["area_keyword"]
            if kktix_area_keyword is None:
                kktix_area_keyword = ""
            kktix_area_keyword = str(kktix_area_keyword).strip()

        if 'area_exclude_keyword' in config_dict["kktix"]:
            kktix_area_exclude_keyword = config_dict["kktix"]["area_exclude_keyword"]
            if kktix_area_exclude_keyword is None:
                kktix_area_exclude_keyword = ""
            kktix_area_exclude_keyword = str(kktix_area_exclude_keyword).strip()

        if 'answer_dictionary' in config_dict["kktix"]:
            kktix_answer_dictionary = config_dict["kktix"]["answer_dictionary"]
            if kktix_answer_dictionary is None:
                kktix_answer_dictionary = ""
            kktix_answer_dictionary = str(kktix_answer_dictionary).strip()

            if len(kktix_answer_dictionary) > 0:
                kktix_answer_dictionary_list = [x.strip() for x in kktix_answer_dictionary.split(',') if x.strip()]

    # for ["tixcraft"]
    date_keyword = ""
    area_keyword = ""
    captcha_assist_enabled = False
    captcha_auto_ocr_enabled = False
    captcha_prompt_timeout_s = 60
    captcha_max_retries = 3
    auto_press_confirm_button_enabled = False
    if 'tixcraft' in config_dict:
        date_cfg = config_dict["tixcraft"].get("date_auto_select", {})
        date_auto_select_enable = bool(date_cfg.get("enable", True))
        date_auto_select_mode = str(date_cfg.get("mode", CONST_SELECT_ORDER_DEFAULT)).strip()

        if date_auto_select_mode not in CONST_SELECT_OPTIONS_ARRAY:
            date_auto_select_mode = CONST_SELECT_ORDER_DEFAULT

        if 'date_keyword' in date_cfg and date_cfg["date_keyword"] is not None:
            date_keyword = str(date_cfg["date_keyword"]).strip()

        area_cfg = config_dict["tixcraft"].get("area_auto_select", {})
        area_auto_select_enable = bool(area_cfg.get("enable", True))
        area_auto_select_mode = str(area_cfg.get("mode", CONST_SELECT_ORDER_DEFAULT)).strip()

        if area_auto_select_mode not in CONST_SELECT_OPTIONS_ARRAY:
            area_auto_select_mode = CONST_SELECT_ORDER_DEFAULT

        if 'area_keyword' in area_cfg and area_cfg["area_keyword"] is not None:
            area_keyword = str(area_cfg["area_keyword"]).strip()

        captcha_assist_enabled = bool(config_dict["tixcraft"].get("captcha_assist", False))
        captcha_auto_ocr_enabled = bool(config_dict["tixcraft"].get("captcha_auto_ocr", False))
        auto_press_confirm_button_enabled = bool(config_dict["tixcraft"].get("auto_press_confirm_button", False))
        try:
            captcha_prompt_timeout_s = max(int(config_dict["tixcraft"].get("captcha_prompt_timeout_s", 60)), 1)
        except (TypeError, ValueError):
            captcha_prompt_timeout_s = 60
        try:
            captcha_max_retries = max(int(config_dict["tixcraft"].get("captcha_max_retries", 3)), 1)
        except (TypeError, ValueError):
            captcha_max_retries = 3

    # entry point
    # 說明：自動開啟第一個的網頁
    if homepage is None or len(str(homepage).strip()) == 0:
        homepage = "https://tixcraft.com/activity/"
    else:
        homepage = str(homepage).strip()

    # output config:
    print("version", CONST_APP_VERSION)
    print("homepage", homepage)
    print("browser", browser)
    print("browser_debug_address", browser_debug_address)
    print("ticket_number", ticket_number)
    print("facebook_account", facebook_account)

    # for kktix
    print("==[kktix]==")
    print("auto_press_next_step_button", auto_press_next_step_button)
    print("auto_fill_ticket_number", auto_fill_ticket_number)
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

    return config_dict


def create_driver(browser_name=None, headless=False, debug_address=None):
    target_browser = (browser_name or browser or "chrome").strip().lower()
    root_dir = get_app_root()
    is_windows = platform.system() == "Windows"

    # 決定是否要「附加」到已開啟的 Chrome（remote debugging）。
    attach_address = ""
    if debug_address is not None:
        attach_address = str(debug_address).strip()
    elif browser_debug_address:
        attach_address = str(browser_debug_address).strip()

    if target_browser == "chrome":
        driver_filename = "chromedriver.exe" if is_windows else "chromedriver"
        chromedriver_path = os.path.join(root_dir, "webdriver", driver_filename)

        chrome_options = webdriver.ChromeOptions()
        chrome_options.page_load_strategy = "eager"
        chrome_options.unhandled_prompt_behavior = "ignore"

        if attach_address:
            # 附加到已手動開啟（並已通過 Cloudflare / 登入）的 Chrome，
            # 不再由程式啟動新的 Chrome。
            # 注意：attach 模式下 chromedriver 不接受 excludeSwitches 等 launch-only
            # 選項（新版 chromedriver 會回 "unrecognized chrome option"），所以這裡
            # 不加 excludeSwitches。
            print("Attaching to existing Chrome via remote debugging: %s" % attach_address)
            chrome_options.add_experimental_option("debuggerAddress", attach_address)
        else:
            chrome_options.add_experimental_option("excludeSwitches", ['enable-automation'])
            if headless:
                chrome_options.add_argument("--headless=new")
                chrome_options.add_argument("--no-sandbox")
                chrome_options.add_argument("--disable-dev-shm-usage")
            else:
                for ext_name in ("AdBlock.crx", "BlockYourselfFromAnalytics.crx"):
                    extension_path = os.path.join(root_dir, "webdriver", ext_name)
                    if os.path.isfile(extension_path):
                        chrome_options.add_extension(extension_path)
                    else:
                        print("extension not exist:", extension_path)

        if os.path.isfile(chromedriver_path):
            service = ChromeService(executable_path=chromedriver_path)
            return webdriver.Chrome(service=service, options=chrome_options)
        # Fall back to Selenium 4 Selenium Manager when local driver binary is absent.
        return webdriver.Chrome(options=chrome_options)

    if target_browser == "firefox":
        if attach_address:
            raise ValueError(
                "browser_debug_address is only supported for 'chrome'; "
                "firefox attach is not implemented."
            )

        driver_filename = "geckodriver.exe" if is_windows else "geckodriver"
        geckodriver_path = os.path.join(root_dir, "webdriver", driver_filename)

        firefox_options = webdriver.FirefoxOptions()
        firefox_options.page_load_strategy = "eager"
        firefox_options.unhandled_prompt_behavior = "ignore"
        if headless:
            firefox_options.add_argument("-headless")

        if os.path.isfile(geckodriver_path):
            service = FirefoxService(executable_path=geckodriver_path)
            return webdriver.Firefox(service=service, options=firefox_options)
        return webdriver.Firefox(options=firefox_options)

    raise ValueError("Unsupported browser: %s (expected 'chrome' or 'firefox')" % target_browser)

# common functions.
def find_between( s, first, last ):
    try:
        start = s.index( first ) + len( first )
        end = s.index( last, start )
        return s[start:end]
    except ValueError:
        return ""

# convert web string to reg pattern
def convert_string_to_pattern(my_str, dynamic_length=True):
    my_hint_anwser_length = len(my_str)
    my_formated = ""
    if my_hint_anwser_length > 0:
        my_anwser_symbols = u"()[]<>{}-"
        for idx in range(my_hint_anwser_length):
            char = my_str[idx:idx+1]

            if char in my_anwser_symbols:
                my_formated += (u'\\' + char)
                continue

            pattern = re.compile(u"[A-Z]")
            match_result = pattern.match(char)
            #print("match_result A:", match_result)
            if not match_result is None:
                my_formated += u"[A-Z]"

            pattern = re.compile(u"[a-z]")
            match_result = pattern.match(char)
            #print("match_result a:", match_result)
            if not match_result is None:
                my_formated += u"[a-z]"

            pattern = re.compile(r"[\d]")
            match_result = pattern.match(char)
            #print("match_result d:", match_result)
            if not match_result is None:
                my_formated += r"[\d]"

        # for dynamic length
        if dynamic_length:
            for i in range(10):
                my_formated = my_formated.replace(u"[A-Z][A-Z]",u"[A-Z]")
                my_formated = my_formated.replace(u"[a-z][a-z]",u"[a-z]")
                my_formated = my_formated.replace(r"[\d][\d]",r"[\d]")

            my_formated = my_formated.replace(u"[A-Z]",u"[A-Z]+")
            my_formated = my_formated.replace(u"[a-z]",u"[a-z]+")
            my_formated = my_formated.replace(r"[\d]",r"[\d]+")
    return my_formated

def get_answer_list_by_question(captcha_text_div_text):
    return_list = None
    my_answer_delimitor = ""

    #if u"?" in captcha_text_div_text or u"？" in captcha_text_div_text:
    if True:
        tmp_text = captcha_text_div_text
        tmp_text = tmp_text.replace(u'  ',u' ')
        tmp_text = tmp_text.replace(u'：',u':')
        # for hint
        tmp_text = tmp_text.replace(u'*',u'*')

        # replace ex.
        tmp_text = tmp_text.replace(u'例如',u'範例')
        tmp_text = tmp_text.replace(u'如:',u'範例:')
        tmp_text = tmp_text.replace(u'舉例',u'範例')
        if not u'範例' in tmp_text:
            tmp_text = tmp_text.replace(u'例',u'範例')
        # important, maybe 例 & ex occurs at same time.
        tmp_text = tmp_text.replace(u'ex:',u'範例:')
        tmp_text = tmp_text.replace(u'Ex:',u'範例:')

        #tmp_text = tmp_text.replace(u'[',u'(')
        #tmp_text = tmp_text.replace(u']',u')')
        tmp_text = tmp_text.replace(u'?',u'？')

        tmp_text = tmp_text.replace(u'（',u'(')
        tmp_text = tmp_text.replace(u'）',u')')

        # is need to convert . ? I am not sure!
        tmp_text = tmp_text.replace(u'。',u' ')

        my_question = ""
        my_options = ""
        my_hint = ""
        my_hint_anwser = ""
        my_anwser_formated = ""

        if u"？" in tmp_text:
            question_index = tmp_text.find(u"？")
            my_question = tmp_text[:question_index+1]
        if u"。" in tmp_text:
            question_index = tmp_text.find(u"。")
            my_question = tmp_text[:question_index+1]
        if len(my_question) == 0:
            my_question = tmp_text
        #print(u"my_question:", my_question)

        # get hint from quota.
        hint_list = None
        # ps: hint_list is not options list

        # try rule1:
        if u'(' in tmp_text and u')' in tmp_text and u'範例' in tmp_text:
            #import re
            #print("text:" , re.findall('\([\w]+\)', tmp_text))
            hint_list = re.findall(r'\(.*?\)', tmp_text)
            #print("hint_list:", hint_list)
        
        # try rule2:
        if hint_list is None:
            if u'【' in tmp_text and u'】' in tmp_text and u'範例' in tmp_text:
                #import re
                #print("text:" , re.findall('\([\w]+\)', tmp_text))
                hint_list = re.findall(u'【.*?】', tmp_text)
        
        # try rule3:
        if not hint_list is None:
            for hint in hint_list:
                if u'範例' in hint:
                    my_hint = hint
                    if my_hint[:1] == u'【':
                        my_hint = my_hint[1:]
                    if my_hint[-1:] == u'】':
                        my_hint = my_hint[:-1]
                    break;
                else:
                    # get hint from rule 3: with '(' & '), but ex: is outside
                    if u'半形' in hint:
                        hint_index = tmp_text.find(hint)
                        ex_index = tmp_text.find(u"範例")
                        if ex_index > 0:
                            ex_end_index = tmp_text.find(u" ",ex_index)
                            if ex_end_index < 0:
                                ex_end_index = tmp_text.find(u"(",ex_index)
                            if ex_end_index < 0:
                                ex_end_index = tmp_text.find(u"（",ex_index)
                            if ex_end_index < 0:
                                ex_end_index = tmp_text.find(u".",ex_index)
                            if ex_end_index < 0:
                                ex_end_index = tmp_text.find(u"。",ex_index)
                            if ex_end_index >=0:
                                my_hint = tmp_text[hint_index:ex_end_index+1]


        # try rule4:
        # get hint from rule 3: without '(' & '), but use "*"
        if len(my_hint) == 0:
            target_symbol = u"*"
            if target_symbol in tmp_text :
                star_index = tmp_text.find(target_symbol)
                space_index = tmp_text.find(u" ", star_index + len(target_symbol))
                my_hint = tmp_text[star_index: space_index]

        # is need to merge next block
        if len(my_hint) > 0:
            target_symbol = my_hint + u" "
            if target_symbol in tmp_text :
                star_index = tmp_text.find(target_symbol)
                next_block_index = star_index + len(target_symbol)
                space_index = tmp_text.find(u" ", next_block_index)
                next_block = tmp_text[next_block_index: space_index]
                if u'範例' in next_block:
                    my_hint += u' ' + next_block 

        if len(my_hint) > 0:
            my_hint_anwser = my_hint[my_hint.find(u"範例")+2:].strip()
            
            if u'答案' in my_hint_anwser and u'填入' in my_hint_anwser:
                # 答案為B需填入Bb)
                fill_index = my_hint_anwser.find(u"填入")
                my_hint_anwser = my_hint_anwser[fill_index+2:].strip()

            if my_hint_anwser[:1] == u":":
                my_hint_anwser = my_hint_anwser[1:]
            if my_hint[:1] == u"(":
                if my_hint_anwser[-1:] == u")":
                    my_hint_anwser = my_hint_anwser[:-1]
            if my_hint_anwser[-1:] == u"。":
                my_hint_anwser = my_hint_anwser[:-1]
        #print(u"my_hint_anwser:", my_hint_anwser)

        # try rule5:
        # get hint from rule 3: n個半形英文大寫
        if len(my_hint) == 0:
            target_symbol = u"個半形英文大寫"
            if target_symbol in tmp_text :
                star_index = tmp_text.find(target_symbol)
                space_index = tmp_text.find(u" ", star_index)
                answer_char_count = tmp_text[star_index-1:star_index]
                if answer_char_count.isnumeric():
                    star_index -= 1
                    my_hint_anwser = u'A' * int(answer_char_count)
                my_hint = tmp_text[star_index: space_index]

            target_symbol = u"個英文大寫"
            if target_symbol in tmp_text :
                star_index = tmp_text.find(target_symbol)
                space_index = tmp_text.find(u" ", star_index)
                answer_char_count = tmp_text[star_index-1:star_index]
                if answer_char_count.isnumeric():
                    star_index -= 1
                    my_hint_anwser = u'A' * int(answer_char_count)
                my_hint = tmp_text[star_index: space_index]

            target_symbol = u"個半形英文小寫"
            if target_symbol in tmp_text :
                star_index = tmp_text.find(target_symbol)
                space_index = tmp_text.find(u" ", star_index)
                answer_char_count = tmp_text[star_index-1:star_index]
                if answer_char_count.isnumeric():
                    star_index -= 1
                    my_hint_anwser = u'a' * int(answer_char_count)
                my_hint = tmp_text[star_index: space_index]

            target_symbol = u"個英文小寫"
            if target_symbol in tmp_text :
                star_index = tmp_text.find(target_symbol)
                space_index = tmp_text.find(u" ", star_index)
                answer_char_count = tmp_text[star_index-1:star_index]
                if answer_char_count.isnumeric():
                    star_index -= 1
                    my_hint_anwser = u'a' * int(answer_char_count)
                my_hint = tmp_text[star_index: space_index]

        if len(my_hint) > 0:
            my_anwser_formated = convert_string_to_pattern(my_hint_anwser)

        # try rule6:
        # get hint from rule 3: n個英數半形字
        if len(my_hint) == 0:
            target_symbol = u"個英數半形字"
            if target_symbol in tmp_text :
                star_index = tmp_text.find(target_symbol)
                space_index = tmp_text.find(u" ", star_index)
                answer_char_count = tmp_text[star_index-1:star_index]
                if answer_char_count.isnumeric():
                    star_index -= 1
                    my_anwser_formated = r'[A-Za-z\d]' * int(answer_char_count)
                my_hint = tmp_text[star_index: space_index]

        if len(my_hint) == 0:
            target_symbol = u"個半形"
            if target_symbol in tmp_text :
                star_index = tmp_text.find(target_symbol)
                space_index = tmp_text.find(u" ", star_index)
                answer_char_count = tmp_text[star_index-1:star_index]
                if answer_char_count.isnumeric():
                    star_index -= 1
                    my_anwser_formated = r'[A-Za-z\d]' * int(answer_char_count)
                my_hint = tmp_text[star_index: space_index]

        #print(u"my_hint:", my_hint)

        #print(u"my_anwser_formated:", my_anwser_formated)

        my_options = tmp_text
        my_options = my_options.replace(my_question,u"")
        my_options = my_options.replace(my_hint,u"")

        # try rule7:
        # check is chinese/english in question, if match, apply my_options rule.
        if len(my_hint) > 0:
            tmp_text_org = captcha_text_div_text
            if u'範例:' in tmp_text:
                tmp_text_org = tmp_text_org.replace(u'Ex:','ex:')
                target_symbol = u"ex:"
                if target_symbol in tmp_text_org :
                    star_index = tmp_text_org.find(target_symbol)
                    my_options = tmp_text_org[star_index-1:]

        #print(u"my_options:", my_options)

        if len(my_anwser_formated) > 0:
            allow_delimitor_symbols = ")].: }"
            pattern = re.compile(my_anwser_formated)
            search_result = pattern.search(my_options)
            if not search_result is None:
                (span_start, span_end) = search_result.span()
                maybe_delimitor = ""
                if len(my_options) > (span_end+1)+1:
                    maybe_delimitor = my_options[span_end+0:span_end+1]
                if len(maybe_delimitor) > 0 and maybe_delimitor in allow_delimitor_symbols:
                    my_answer_delimitor = maybe_delimitor
        #print(u"my_answer_delimitor:", my_answer_delimitor)



        # try all possible options.
        tmp_text = captcha_text_div_text
        tmp_text = tmp_text.replace(u'  ',u' ')
        tmp_text = tmp_text.replace(u'例如',u'範例')
        tmp_text = tmp_text.replace(u'例:',u'範例')
        tmp_text = tmp_text.replace(u'如:',u'範例')
        tmp_text = tmp_text.replace(u'舉例',u'範例')
        #tmp_text = tmp_text.replace(u'[',u'(')
        #tmp_text = tmp_text.replace(u']',u')')

        if len(my_anwser_formated) > 0:
            #print("text:" , re.findall('\([\w]+\)', tmp_text))
            new_pattern = my_anwser_formated
            if len(my_answer_delimitor) > 0:
                new_pattern = my_anwser_formated + u'\\' + my_answer_delimitor
            return_list = re.findall(new_pattern, my_options)

            if not return_list is None:
                if len(return_list) == 1:
                    # re-sample for this case.
                    return_list = re.findall(my_anwser_formated, my_options)

        # try rule8:
        if return_list is None:
            # need replace to space to get first options.
            tmp_text = captcha_text_div_text
            tmp_text = tmp_text.replace(u'?',u' ')
            tmp_text = tmp_text.replace(u'？',u' ')
            tmp_text = tmp_text.replace(u'。',u' ')

            delimitor_symbols_left = [u"(",u"[",u"{", " ", " ", " ", " "]
            delimitor_symbols_right = [u")",u"]",u"}", ":", ".", ")", "-"]
            idx = -1
            for idx in range(len(delimitor_symbols_left)):
                symbol_left = delimitor_symbols_left[idx]
                symbol_right = delimitor_symbols_right[idx]
                if symbol_left in tmp_text and symbol_right in tmp_text and u'半形' in tmp_text:
                    hint_list = re.findall(u'\\'+ symbol_left + u'[\\w]+\\'+ symbol_right , tmp_text)
                    #print("hint_list:", hint_list)
                    if not hint_list is None:
                        if len(hint_list) > 1:
                            return_list = []
                            my_answer_delimitor = symbol_right
                            for options in hint_list:
                                if len(options) > 2:
                                    my_anwser = options[1:-1]
                                    #print("my_anwser:",my_anwser)
                                    if len(my_anwser) > 0:
                                        return_list.append(my_anwser)
                
                if not return_list is None:
                    break
    #print("return_list:", return_list)
    return return_list, my_answer_delimitor

def _select_target_index(items_len, mode):
    if items_len <= 0:
        return -1
    if mode == CONST_FROM_BOTTOM_TO_TOP:
        return items_len - 1
    if mode == CONST_RANDOM:
        return random.randint(0, items_len - 1)
    return 0


_diag_counts = {}


def _date_diag(msg):
    # Diagnostic output for the date page. The main loop runs every 0.1s, so
    # each distinct message is printed at most 3 times to avoid flooding.
    count = _diag_counts.get(msg, 0) + 1
    _diag_counts[msg] = count
    if count <= 3:
        print("[diag]", msg)
    elif count == 4:
        print("[diag] (repeated, suppressing):", msg)


def _describe_button(btn):
    try:
        return "tag=%s class=%r text=%r data-href=%r enabled=%s displayed=%s" % (
            btn.tag_name,
            btn.get_attribute("class"),
            (btn.text or "").strip(),
            btn.get_attribute("data-href"),
            btn.is_enabled(),
            btn.is_displayed(),
        )
    except Exception as exc:
        return "describe fail: %s" % exc


def _is_tixcraft_game_button(btn):
    if not btn.is_enabled():
        return False
    cls = (btn.get_attribute('class') or '').split()
    if 'search-btn' in cls:
        return False
    data_href = btn.get_attribute('data-href')
    if data_href is not None and '/ticket/' not in data_href:
        return False
    return True


def _find_tixcraft_game_buttons(scope):
    for selector in ('.btn-next', 'button[data-href]', 'button.btn-primary', 'a.btn-primary'):
        try:
            buttons = scope.find_elements(By.CSS_SELECTOR, selector)
            enabled_buttons = [btn for btn in buttons if _is_tixcraft_game_button(btn)]
            if enabled_buttons:
                return enabled_buttons
        except Exception:
            pass
    return []


def _click_tixcraft_game_button(el, current_url):
    try:
        el.click()
        return True
    except Exception as exc:
        print("try to click game button fail:", exc)
        try:
            data_href = el.get_attribute('data-href')
            if data_href:
                if data_href.startswith('http://') or data_href.startswith('https://'):
                    driver.get(data_href)
                else:
                    parsed = urlparse(current_url)
                    base = "%s://%s" % (parsed.scheme, parsed.netloc)
                    if not data_href.startswith('/'):
                        data_href = '/' + data_href
                    driver.get(base + data_href)
                return True
        except Exception as exc2:
            print("fallback navigate data-href fail:", exc2)
    return False


# from detail to game
def tixcraft_redirect(url):
    parsed = urlparse(url)
    path_parts = [p for p in parsed.path.split("/") if p]
    if len(path_parts) >= 3 and path_parts[0] == "activity" and path_parts[1] == "detail":
        game_name = path_parts[2]
        entry_url = "%s://%s/activity/game/%s" % (parsed.scheme, parsed.netloc, game_name)
        driver.get(entry_url)
        return True
    return False


def date_auto_select(url):
    parsed = urlparse(url)
    path_parts = [p for p in parsed.path.split("/") if p]

    # choose date
    if len(path_parts) >= 3 and path_parts[0] == "activity" and path_parts[1] == "game":
        clicked = False
        if len(date_keyword) == 0:
            game_scope = driver
            try:
                game_scope = driver.find_element(By.ID, 'gameList')
            except Exception:
                pass
            buttons = _find_tixcraft_game_buttons(game_scope)
            target_idx = _select_target_index(len(buttons), date_auto_select_mode)
            _date_diag("date page %s: buttons=%d target_idx=%d mode=%s" % (url, len(buttons), target_idx, date_auto_select_mode))
            if target_idx >= 0:
                _date_diag("date target button: " + _describe_button(buttons[target_idx]))
                clicked = _click_tixcraft_game_button(buttons[target_idx], url)
                _date_diag("date click result: clicked=%s (url before click: %s)" % (clicked, url))
        else:
            # match keyword.
            date_list = None
            try:
                date_list = driver.find_elements(By.CSS_SELECTOR, '#gameList table tbody tr')
            except Exception as exc:
                print("find #gameList fail")

            if date_list:
                matched_buttons = []
                for row in date_list:
                    row_text = ""
                    try:
                        row_text = row.text
                    except Exception as exc:
                        print("get text fail")
                        break

                    if len(row_text) > 0 and date_keyword in row_text:
                        row_buttons = _find_tixcraft_game_buttons(row)
                        if row_buttons:
                            matched_buttons.append(row_buttons[0])
                            if date_auto_select_mode == CONST_FROM_TOP_TO_BOTTOM:
                                break

                target_idx = _select_target_index(len(matched_buttons), date_auto_select_mode)
                _date_diag("date page %s: keyword=%r rows=%d matched=%d target_idx=%d" % (
                    url, date_keyword, len(date_list) if date_list else 0, len(matched_buttons), target_idx))
                if target_idx >= 0:
                    _date_diag("date target button: " + _describe_button(matched_buttons[target_idx]))
                    clicked = _click_tixcraft_game_button(matched_buttons[target_idx], url)
                    _date_diag("date click result: clicked=%s (url before click: %s)" % (clicked, url))

        if clicked:
            return True

        # auto refresh for date list page when no target button is available yet.
        _date_diag("date page: no clickable target, refreshing (url=%s)" % url)
        try:
            time.sleep(0.3)
            driver.refresh()
        except Exception as exc:
            pass
    return False


# PS: auto refresh condition 1: no keyword + no hyperlink.
# PS: auto refresh condition 2: with keyword + no matching hyperlink.
def area_auto_select(url):
    parsed = urlparse(url)
    if '/ticket/area/' in parsed.path:
        #driver.switch_to.default_content()

        el = None
        for selector in ('.zone', '.area-list', '#select_form_auto'):
            try:
                el = driver.find_element(By.CSS_SELECTOR, selector)
                if el is not None:
                    break
            except Exception:
                pass
        if el is None:
            print("find .zone fail, do nothing.")

        if el is not None:
            areas = []
            is_need_refresh = False

            area_list = None
            try:
                area_list = el.find_elements(By.TAG_NAME, "a")
            except Exception as exc:
                pass

            if area_list is not None:
                for row in area_list:
                    row_is_enabled = False
                    try:
                        row_is_enabled = row.is_enabled()
                    except Exception as exc:
                        pass

                    if not row_is_enabled:
                        continue

                    if len(area_keyword) == 0:
                        areas.append(row)
                    else:
                        row_text = ""
                        try:
                            row_text = row.text
                        except Exception as exc:
                            print("get text fail")
                            break

                        if len(row_text) > 0 and area_keyword in row_text:
                            areas.append(row)
                            if area_auto_select_mode == CONST_FROM_TOP_TO_BOTTOM:
                                print("only need first item, break area list loop.")
                                break

            if len(areas) == 0:
                if len(area_keyword) == 0:
                    print("list is empty, do refresh!")
                else:
                    print("(with keyword) no matching area, do refresh!")
                is_need_refresh = True

            area_target = None
            if len(areas) > 0:
                target_row_index = _select_target_index(len(areas), area_auto_select_mode)
                area_target = areas[target_row_index]

            if area_target is not None:
                try:
                    print("area text", area_target.text)
                    area_target.click()
                    return True
                except Exception as exc:
                    print("click area a link fail, start to retry...")
                    time.sleep(0.2)
                    try:
                        driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", area_target)
                        area_target.click()
                        return True
                    except Exception as exc2:
                        try:
                            driver.execute_script("arguments[0].click();", area_target)
                            return True
                        except Exception as exc3:
                            print("click area a link fail, after retry still fail.")
                            print(exc3)

            # auto refresh for area list page.
            if is_need_refresh:
                try:
                    time.sleep(0.3)
                    driver.refresh()
                except Exception as exc:
                    pass
    return False

'''
        el_selectSeat_iframe = None
        try:
            el_selectSeat_iframe = driver.find_element_by_xpath("//iframe[contains(@src,'/ticket/selectSeat/')]")
        except Exception as exc:
            #print("find seat iframe fail")
            pass

        if el_selectSeat_iframe is not None:
            driver.switch_to.frame(el_selectSeat_iframe)
            
            # click one seat
            el_seat = None
            try:
                el_seat = driver.find_element(By.CSS_SELECTOR, '.empty')
                if el_seat is not None:
                    try:
                        el_seat.click()
                    except Exception as exc:
                        #print("click area button fail")
                        pass
            except Exception as exc:
                print("find empty seat fail")


            # click submit button
            el_confirm_seat = None
            try:
                el_confirm_seat = driver.find_element(By.ID, 'submitSeat')
                if el_confirm_seat is not None:
                    try:
                        el_confirm_seat.click()
                    except Exception as exc:
                        #print("click area button fail")
                        pass
            except Exception as exc:
                print("find submitSeat fail")
'''

def ticket_number_auto_fill(url, form_select):
    # check agree
    form_checkbox = None
    try:
        form_checkbox = driver.find_element(By.ID, 'TicketForm_agree')

        if form_checkbox is not None and not form_checkbox.is_selected():
            try:
                form_checkbox.click()
            except Exception as exc:
                print("click TicketForm_agree fail")
    except Exception as exc:
        print("find TicketForm_agree fail")

    # 使用 plan B: only set via JS if checkbox is still unchecked.
    try:
        if form_checkbox is None or not form_checkbox.is_selected():
            driver.execute_script(
                'var cb = document.getElementById("TicketForm_agree");'
                'if (cb && !cb.checked) { cb.checked = true; cb.dispatchEvent(new Event("change", {bubbles: true})); }'
            )
    except Exception as exc:
        print("javascript check TicketForm_agree fail")
        print(exc)

    # select options
    select = None
    try:
        select = Select(form_select)
    except Exception as exc:
        print("select fail")

    if select is not None:
        selected = False
        for attempt in (
            lambda: select.select_by_visible_text(ticket_number),
            lambda: select.select_by_value(ticket_number),
            lambda: select.select_by_visible_text("1"),
            lambda: select.select_by_value("1"),
        ):
            try:
                attempt()
                selected = True
                break
            except Exception as exc:
                print("select ticket_number attempt fail:", exc)
        if not selected:
            print("unable to select ticket_number:", ticket_number)

    # Focus verify code input so the user can enter the verification code manually.
    form_verifyCode = None
    try:
        form_verifyCode = driver.find_element(By.ID, 'TicketForm_verifyCode')
        if form_verifyCode is not None:
            try:
                form_verifyCode.click()
            except Exception as exc:
                print("click form_verifyCode fail")
    except Exception as exc:
        print("find form_verifyCode fail")

def tixcraft_verify(url):
    ret = False

    captcha_password_string = None

    form_select = None
    try:
        form_select = driver.find_element(By.CSS_SELECTOR, '.zone-verify')


        if form_select is not None:
            html_text = ""
            try:
                html_text = form_select.text

                html_text = html_text.replace(u'「',u'【')
                html_text = html_text.replace(u'〔',u'【')
                html_text = html_text.replace(u'［',u'【')
                html_text = html_text.replace(u'〖',u'【')
                html_text = html_text.replace(u'[',u'【')

                html_text = html_text.replace(u'」',u'】')
                html_text = html_text.replace(u'〕',u'】')
                html_text = html_text.replace(u'］',u'】')
                html_text = html_text.replace(u'〗',u'】')
                html_text = html_text.replace(u']',u'】')

                #print("html_text:", html_text)
                if u'【' in html_text and u'】' in html_text:
                    #captcha_password_string = find_between(html_text, u"【", u"】")
                    pass
            except Exception as exc:
                print("get text fail")


    except Exception as exc:
        print("find verify fail")
        pass

    
    if not captcha_password_string is None:
        form_input = None
        try:
            form_input = driver.find_element(By.CSS_SELECTOR, '#checkCode')
            if form_input is not None:
                default_value = form_input.get_attribute('value')
                if not default_value is None:
                    if len(default_value) == 0:
                        form_input.send_keys(captcha_password_string)
                        print("send captcha keys:" + captcha_password_string)
                        time.sleep(0.2)
                        ret = True
            else:
                print("find captcha input field fail")

        except Exception as exc:
            print("find verify fail")
            pass

    if ret:
        # retry
        for i in range(5):
            form_input = None
            try:
                form_input = driver.find_element(By.CSS_SELECTOR, '#submitButton')
                if form_input is not None:
                    if form_input.is_enabled():
                        form_input.click()
                        break
                else:
                    print("find submit button none")

            except Exception as exc:
                print("find submit button fail")
                print(exc)
                pass

    return ret


def _run_captcha_assist(driver_instance):
    if not (captcha_assist_enabled or captcha_auto_ocr_enabled):
        return None

    # Any failure must fall back to manual entry; never abort the purchase loop.
    try:
        assist = CaptchaAssist(
            timeout_s=captcha_prompt_timeout_s,
            max_retries=captcha_max_retries,
            auto_ocr=captcha_auto_ocr_enabled,
            prompt_enabled=captcha_assist_enabled,
        )
        return assist.run(driver_instance)
    except Exception as exc:
        print("CAPTCHA assist failed: %s" % exc)
        return None


CONFIRM_TICKET_BUTTON_SELECTORS = (
    "#TicketForm_submit",
    '#TicketForm button[type="submit"]',
    '#TicketForm input[type="submit"]',
    "#TicketForm button.btn-primary",
    "#TicketForm a.btn-primary",
    "#TicketForm .btn-primary",
)
CONFIRM_TICKET_BUTTON_TEXTS = ("確認張數", "確認", "下一步", "送出", "立即訂購")


def _click_confirm_button_element(el):
    try:
        el.click()
        return True
    except Exception:
        pass
    try:
        driver.execute_script(
            "arguments[0].scrollIntoView({block: 'center'}); arguments[0].click();",
            el,
        )
        return True
    except Exception:
        return False


def tixcraft_press_confirm_button():
    """Find and click the tixCraft '確認張數' (confirm quantity) button."""
    ret = False

    # 1) Try known selectors first.
    for selector in CONFIRM_TICKET_BUTTON_SELECTORS:
        try:
            el = driver.find_element(By.CSS_SELECTOR, selector)
        except Exception:
            continue
        if el is not None and el.is_enabled() and _click_confirm_button_element(el):
            ret = True
            break

    # 2) Fall back to matching the button by its visible text.
    if not ret:
        try:
            candidates = driver.find_elements(By.CSS_SELECTOR, 'button, a.btn, input[type="submit"]')
            for el in candidates:
                try:
                    text = (el.text or "").strip()
                    if text in CONFIRM_TICKET_BUTTON_TEXTS and el.is_enabled() and _click_confirm_button_element(el):
                        ret = True
                        break
                except Exception:
                    continue
        except Exception as exc:
            print("find confirm ticket button fail:", exc)

    if not ret:
        print("confirm ticket quantity button not found")
    return ret


def tixcraft_ticket_main(url, is_verifyCode_editing):
    form_select = None
    for selector in ('.mobile-select', 'select[id^="TicketForm_ticketPrice"]', '#TicketForm select'):
        try:
            form_select = driver.find_element(By.CSS_SELECTOR, selector)
            if form_select is not None:
                break
        except Exception:
            pass

    if form_select is None:
        print("find select fail")
        return is_verifyCode_editing

    try:
        selected_option = Select(form_select).first_selected_option
        if selected_option.text.strip() == "0" or selected_option.get_attribute("value") == "0":
            is_verifyCode_editing = False
    except Exception as exc:
        print("query selected option fail")
        print(exc)

    if is_verifyCode_editing == False:
        ticket_number_auto_fill(url, form_select)

        # Opt-in only. By default the order form is never submitted here: the
        # user still reviews the filled code and confirms the order and payment.
        if captcha_assist_enabled or captcha_auto_ocr_enabled:
            if not _run_captcha_assist(driver):
                print("CAPTCHA assist did not fill the code; continuing with manual entry")

        # Keep focus on the verification input for review or manual fallback.
        try:
            driver.execute_script(
                'var vc = document.getElementById("TicketForm_verifyCode"); if (vc) { vc.focus(); }'
            )

            is_verifyCode_editing = True
            print("goto is_verifyCode_editing== True")
        except Exception as exc:
            print(exc)

        # Optionally auto-press the "確認張數" (confirm quantity) button once
        # the quantity, agreement and verification code have been filled.
        if auto_press_confirm_button_enabled:
            if tixcraft_press_confirm_button():
                print("pressed confirm ticket quantity button")
    else:
        #print("is_verifyCode_editing")
        # do nothing here.
        pass

    return is_verifyCode_editing

def _parse_keywords(keyword_str):
    if not keyword_str:
        return []
    # Split on delimiters (comma/semicolon, ASCII or full-width) while preserving
    # thousands-separator commas inside numbers such as "$3,800".
    parts = re.split(r'(?<!\d),|,(?!\d{3}(?:\D|$))|[，;；]+', str(keyword_str))
    return [part.strip() for part in parts if part.strip()]


def _normalize_kktix_match_text(text):
    if not text:
        return ""
    # Normalize case and remove thousands-separator commas inside numbers so
    # "$3800", "$3,800", and "TWD$3,800" all match consistently.
    normalized = re.sub(r'(?<=\d),(?=\d{3}(?!\d))', '', str(text))
    return normalized.casefold()


def _kktix_parse_positive_int(value):
    try:
        num = int(str(value).strip())
        return num if num > 0 else 0
    except Exception:
        return 0


def kktix_event_redirect(url):
    parsed = urlparse(url)
    path = parsed.path or ""
    if "/events/" not in path or "/registrations" in path:
        return False

    selectors = (
        'a.btn-point[href*="/registrations/new"]',
        'a[href*="/registrations/new"]',
        'a.btn-point[href*="registrations"]',
    )
    for selector in selectors:
        try:
            links = driver.find_elements(By.CSS_SELECTOR, selector)
            for link in links:
                if not link.is_displayed() or not link.is_enabled():
                    continue
                href = link.get_attribute("href")
                if not href:
                    continue
                # Use driver.get() instead of link.click(): the click is async and
                # the bot may check the ticket list before the registrations page has
                # finished loading, which made it wrongly report "no available".
                try:
                    driver.get(href)
                    return True
                except Exception as exc:
                    print("navigate kktix registrations fail:", exc)
        except Exception:
            pass
    return False


def _kktix_get_row_quantity_input(row):
    selectors = (
        '.ticket-quantity input[type="text"], .ticket-quantity input[type="number"], .ticket-quantity input:not([type])',
        'input[type="text"], input[type="number"], input:not([type])',
    )
    for selector in selectors:
        try:
            inputs = row.find_elements(By.CSS_SELECTOR, selector)
            for inp in inputs:
                inp_type = (inp.get_attribute("type") or "text").strip().lower()
                if inp_type in ("hidden", "checkbox", "radio", "submit", "button"):
                    continue
                if not inp.is_displayed() or not inp.is_enabled():
                    continue
                if inp.get_attribute("disabled") is not None:
                    continue
                return inp
        except Exception:
            pass
    return None


def _kktix_find_ticket_rows():
    rows = []
    for selector in ('.ticket-unit', '.display-table-row'):
        try:
            found = driver.find_elements(By.CSS_SELECTOR, selector)
            if found:
                rows = found
                break
        except Exception:
            pass

    available = []
    for row in rows:
        try:
            if not row.is_displayed() or not row.is_enabled():
                continue
        except Exception:
            continue

        qty_input = _kktix_get_row_quantity_input(row)
        if qty_input is None:
            continue

        available.append((row, qty_input))
    return available


def _kktix_set_ticket_quantity(row, qty_input, target_qty):
    current_val = _kktix_parse_positive_int(qty_input.get_attribute('value'))
    if current_val > 0:
        return True

    target_int = _kktix_parse_positive_int(target_qty)
    if target_int <= 0:
        target_int = 1

    candidates = [str(target_int)]
    if target_int != 1:
        candidates.append("1")

    for qty_str in candidates:
        desired = int(qty_str)
        # Strategy A: direct input + input/change events so AngularJS ng-model updates.
        try:
            if qty_input.get_attribute('readonly') is None:
                qty_input.clear()
                qty_input.send_keys(qty_str)
                driver.execute_script(
                    "arguments[0].dispatchEvent(new Event('input', {bubbles: true}));"
                    "arguments[0].dispatchEvent(new Event('change', {bubbles: true}));",
                    qty_input,
                )
                actual = _kktix_parse_positive_int(qty_input.get_attribute('value'))
                if actual == desired:
                    return True
                # Handle inputs that reset empty string to '0' during clear() (e.g. '20').
                driver.execute_script(
                    "arguments[0].value = arguments[1];"
                    "arguments[0].dispatchEvent(new Event('input', {bubbles: true}));"
                    "arguments[0].dispatchEvent(new Event('change', {bubbles: true}));",
                    qty_input,
                    qty_str,
                )
                if _kktix_parse_positive_int(qty_input.get_attribute('value')) == desired:
                    return True
        except Exception as exc:
            print("assign ticket number via input fail:", exc)

        # Strategy B: click plus button if direct typing is unavailable or did not update the value.
        try:
            plus_buttons = row.find_elements(By.CSS_SELECTOR, 'button.plus, .btn-default.plus, .plus')
            plus_btn = next(
                (
                    b for b in plus_buttons
                    if b.is_displayed() and b.is_enabled() and b.get_attribute('disabled') is None
                ),
                None,
            )
            if plus_btn is not None:
                for _ in range(desired):
                    if _kktix_parse_positive_int(qty_input.get_attribute('value')) >= desired:
                        break
                    if not plus_btn.is_enabled() or plus_btn.get_attribute('disabled') is not None:
                        break
                    plus_btn.click()
                if _kktix_parse_positive_int(qty_input.get_attribute('value')) > 0:
                    return True
        except Exception:
            pass

    return False


KKTIX_AGREEMENT_KEYWORDS = (
    'agree', 'accept', 'terms', 'privacy', 'policy',
    '同意', '條款', '隱私', '政策',
)


def _kktix_checkbox_context_text(checkbox):
    texts = []
    try:
        texts.append(checkbox.text or "")
    except Exception:
        pass
    try:
        label = checkbox.find_element(By.XPATH, 'ancestor::label[1]')
        if label is not None:
            texts.append(label.text or "")
    except Exception:
        pass
    try:
        parent = checkbox.find_element(By.XPATH, '..')
        if parent is not None:
            texts.append(parent.text or "")
    except Exception:
        pass
    return " ".join(texts)


def _kktix_is_agreement_checkbox(checkbox):
    try:
        if not checkbox.is_displayed():
            return False
    except Exception:
        return False

    text = _kktix_checkbox_context_text(checkbox)
    normalized = text.casefold()
    return any(keyword.casefold() in normalized for keyword in KKTIX_AGREEMENT_KEYWORDS)


def _kktix_click_agreement_checkbox(checkbox):
    if checkbox is None:
        return False

    try:
        if not checkbox.is_selected():
            checkbox.click()
    except Exception as exc:
        print("click agreement checkbox fail:", exc)

    try:
        if not checkbox.is_selected():
            driver.execute_script(
                "arguments[0].checked = true;"
                "arguments[0].dispatchEvent(new Event('click', {bubbles: true}));"
                "arguments[0].dispatchEvent(new Event('change', {bubbles: true}));",
                checkbox,
            )
        return checkbox.is_selected()
    except Exception as exc:
        print("javascript check agreement checkbox fail:", exc)
        return False


def kktix_agree_terms():
    # Part 1: the known KKTIX checkbox id (門票不可退款 / 服務條款 agreement).
    try:
        checkbox = driver.find_element(By.ID, 'person_agree_terms')
        _kktix_click_agreement_checkbox(checkbox)
    except Exception:
        # Some KKTIX forms do not have a separate terms checkbox.
        pass

    # Part 2: KKTIX renders additional agreement controls dynamically, e.g.
    # "我已經閱讀並同意 服務條款 與 隱私權政策" (checkbox) and
    # "我同意KKTIX系統所分配之門票..." (radio). Check every visible checkbox/radio
    # whose label mentions agreement/terms/privacy so all of them are covered.
    try:
        controls = driver.find_elements(By.CSS_SELECTOR, 'input[type="checkbox"], input[type="radio"]')
        for control in controls:
            if _kktix_is_agreement_checkbox(control):
                _kktix_click_agreement_checkbox(control)
    except Exception as exc:
        print("find agreement checkboxes fail:", exc)

    return True


def kktix_registration_form(url, answer_index):
    """Handle the KKTIX step-2 page (fill registration info / confirm order).

    The URL for this step is ``/registrations/<order_id>`` (not ``/registrations/new``),
    which the main loop routes here. It auto-checks the agreement controls, waits for
    the human-verification / CAPTCHA if present, and then auto-presses the
    "確認表單資料" (confirm) button; the final payment stays manual.
    """
    #---------------------------
    # agree terms / notice (checkbox + radio)
    #---------------------------
    kktix_agree_terms()

    #---------------------------
    # human verification / CAPTCHA check (manual completion)
    #---------------------------
    has_verification, custom_input = kktix_has_human_verification()
    if has_verification:
        captcha_done = False
        if custom_input is not None:
            try:
                captcha_done = len(custom_input.get_attribute('value') or "") > 0
                if not captcha_done:
                    already_focused = custom_input.get_attribute('data-bot-focused') == '1'
                    if not already_focused:
                        driver.execute_script(
                            "arguments[0].setAttribute('data-bot-focused', '1'); arguments[0].focus();",
                            custom_input,
                        )
            except Exception:
                pass
        # Pause until the user completes the verification; the next loop pass will
        # detect the filled code and then press the confirm button.
        if not captcha_done:
            return answer_index

    #---------------------------
    # auto press the confirm button
    #---------------------------
    if auto_press_next_step_button:
        kktix_press_next_button()

    return answer_index


def kktix_is_login_required(app_div=None):
    scope = app_div
    if scope is None:
        try:
            scope = driver.find_element(By.ID, 'registrationsNewApp')
        except Exception:
            return False

    try:
        sign_in_links = scope.find_elements(
            By.CSS_SELECTOR,
            'a[href*="/users/sign_in"], a[href*="sign_in"], button[ng-click*="signIn"], button[ng-click*="login"]',
        )
        for el in sign_in_links:
            if el.is_displayed():
                return True
    except Exception:
        pass

    return False


def kktix_has_human_verification():
    custom_input = None
    try:
        captcha_divs = driver.find_elements(By.CSS_SELECTOR, '.custom-captcha-inner')
        for div in captcha_divs:
            if div.is_displayed():
                try:
                    custom_input = div.find_element(By.TAG_NAME, 'input')
                except Exception:
                    custom_input = None
                return True, custom_input
    except Exception:
        pass

    widget_selectors = (
        '.g-recaptcha',
        'iframe[src*="recaptcha"]',
        '.h-captcha',
        'iframe[src*="hcaptcha"]',
        'iframe[src*="turnstile"]',
        'input[name="cf-turnstile-response"]',
    )
    for selector in widget_selectors:
        try:
            elements = driver.find_elements(By.CSS_SELECTOR, selector)
            for el in elements:
                if el.is_displayed():
                    return True, None
        except Exception:
            pass

    return False, None


KKTIX_NEXT_BUTTON_SELECTORS = (
    '#registrationsNewApp div.form-actions button.btn-primary',
    'div.form-actions button.btn-primary',
    'button.btn-primary[ng-click*="challenge"]',
    'button[type="submit"].btn-primary',
)
# Seated events (e.g. concerts) show "自行選位" (pick your own seat) and
# "電腦配位" (let the system assign seats) instead of a plain "下一步".
# Prefer "電腦配位" because it is the fastest fully-automatic path (no seat map).
KKTIX_PREFERRED_NEXT_BUTTON_TEXTS = (
    '電腦配位',
    '下一步',
    '確認',
)
KKTIX_NEXT_CLICK_COOLDOWN_MS = 1500


def _is_kktix_next_button_clickable(btn):
    try:
        if not btn.is_displayed() or not btn.is_enabled():
            return False
        if btn.get_attribute('disabled') is not None:
            return False
        cls = (btn.get_attribute('class') or '').split()
        if 'disabled' in cls or 'ng-hide' in cls:
            return False
        return True
    except Exception:
        return False


def _find_clickable_kktix_next_button(drv=None):
    target_driver = drv or driver

    # First prefer the automated-path buttons (e.g. "電腦配位") by label text.
    for text in KKTIX_PREFERRED_NEXT_BUTTON_TEXTS:
        try:
            buttons = target_driver.find_elements(By.CSS_SELECTOR, 'button, a.btn, a.btn-primary')
            for btn in buttons:
                try:
                    btn_text = (btn.text or '').strip()
                except Exception:
                    continue
                if text in btn_text and _is_kktix_next_button_clickable(btn):
                    return btn
        except Exception:
            pass

    # Fall back to the generic selectors.
    for selector in KKTIX_NEXT_BUTTON_SELECTORS:
        try:
            buttons = target_driver.find_elements(By.CSS_SELECTOR, selector)
            for btn in buttons:
                if _is_kktix_next_button_clickable(btn):
                    return btn
        except Exception:
            pass
    return False


def kktix_press_next_button():
    # Prevent duplicate clicks while an async Next Step request is already in flight on the same page.
    try:
        within_cooldown = driver.execute_script(
            "var last = window.__kktix_next_clicked_at || 0;"
            "return last > 0 && (Date.now() - last) < arguments[0];",
            KKTIX_NEXT_CLICK_COOLDOWN_MS,
        )
        if within_cooldown:
            return False
    except Exception:
        pass

    next_step_button = None
    try:
        wait = WebDriverWait(driver, 0.8, poll_frequency=0.05)
        next_step_button = wait.until(_find_clickable_kktix_next_button)
    except Exception:
        next_step_button = _find_clickable_kktix_next_button(driver) or None

    if not next_step_button:
        return False

    try:
        driver.execute_script("window.__kktix_next_clicked_at = Date.now();")
    except Exception:
        pass

    try:
        next_step_button.click()
        return True
    except Exception:
        try:
            driver.execute_script(
                "arguments[0].scrollIntoView({block: 'center'}); arguments[0].click();",
                next_step_button,
            )
            return True
        except Exception:
            try:
                driver.execute_script("window.__kktix_next_clicked_at = 0;")
            except Exception:
                pass
            return False


def kktix_captcha_text_value(captcha_inner_div):
    ret = ""

    if captcha_inner_div is not None:
        try:
            captcha_password_text = captcha_inner_div.find_element(By.TAG_NAME, "input")
            if captcha_password_text is not None:
                ret = captcha_password_text.get_attribute('value') or ""
            else:
                print("find captcha input field fail")
        except Exception:
            print("find captcha_inner_div Exception:")
    return ret


def kktix_input_captcha_text(captcha_inner_div, captcha_password_string, force_overwrite=False):
    ret = False

    try:
        if captcha_inner_div is not None and captcha_password_string is not None:
            captcha_password_text = captcha_inner_div.find_element(By.TAG_NAME, "input")
            if captcha_password_text is not None:
                inputed_captcha_text = captcha_password_text.get_attribute('value') or ""
                if force_overwrite or len(inputed_captcha_text) == 0:
                    if force_overwrite:
                        captcha_password_text.clear()
                    captcha_password_text.send_keys(captcha_password_string)
                    print("send captcha keys:" + captcha_password_string)
                    ret = True
            else:
                print("find captcha input field fail")
    except Exception:
        print("find kktix_input_captcha_text Exception:")

    return ret


def kktix_assign_ticket_number():
    available_rows = _kktix_find_ticket_rows()
    if not available_rows:
        return False

    # If a quantity is already selected on any row, keep it.
    for _, qty_input in available_rows:
        try:
            if _kktix_parse_positive_int(qty_input.get_attribute('value')) > 0:
                return True
        except Exception:
            pass

    exclude_keywords = [_normalize_kktix_match_text(kw) for kw in _parse_keywords(kktix_area_exclude_keyword)]
    include_keywords = [_normalize_kktix_match_text(kw) for kw in _parse_keywords(kktix_area_keyword)]

    filtered_rows = []
    for row, qty_input in available_rows:
        row_text = ""
        try:
            row_text = row.text or ""
        except Exception:
            continue

        norm_row_text = _normalize_kktix_match_text(row_text)
        if any(ex_kw in norm_row_text for ex_kw in exclude_keywords):
            continue
        filtered_rows.append((row, qty_input, norm_row_text))

    if not filtered_rows:
        return False

    candidates = []
    if not include_keywords:
        candidates = [(row, qty_input) for row, qty_input, _ in filtered_rows]
    else:
        # Match keywords in priority order; pick the first tier that has available tickets.
        for kw in include_keywords:
            tier = [(row, qty_input) for row, qty_input, norm_row_text in filtered_rows if kw in norm_row_text]
            if tier:
                candidates = tier
                break

    if not candidates:
        return False

    target_row_index = _select_target_index(len(candidates), kktix_area_auto_select_mode)
    if target_row_index < 0:
        return False

    target_row, target_input = candidates[target_row_index]
    return _kktix_set_ticket_quantity(target_row, target_input, ticket_number)


def kktix_reg_new(url, answer_index):
    #---------------------------
    # part 1: check ticket availability & auto refresh
    #---------------------------
    available_rows = _kktix_find_ticket_rows()
    if not available_rows:
        # The KKTIX ticket list is rendered asynchronously by AngularJS after the
        # page navigates (for example after clicking "立即購票" on the event page).
        # Wait briefly for the quantity inputs to appear before giving up and
        # refreshing, otherwise the bot can miss tickets that are actually on sale.
        try:
            WebDriverWait(driver, 3, poll_frequency=0.2).until(
                lambda drv: len(_kktix_find_ticket_rows()) > 0
            )
            available_rows = _kktix_find_ticket_rows()
        except TimeoutException:
            available_rows = []

    if not available_rows:
        # Best-effort login check (only applies to older KKTIX layouts that have
        # the #registrationsNewApp container).
        try:
            app_div = driver.find_element(By.ID, 'registrationsNewApp')
            if app_div is not None and kktix_is_login_required(app_div):
                _date_diag("KKTIX requires login on /registrations/new; pausing auto-refresh for manual sign-in.")
                return answer_index
        except Exception:
            pass

        print("no available KKTIX ticket inputs yet, refreshing...")
        try:
            time.sleep(0.5)
            driver.refresh()
        except Exception:
            pass
        return -1

    #---------------------------
    # part 2: agree terms checkbox
    #---------------------------
    kktix_agree_terms()

    #---------------------------
    # part 3: ticket number
    #---------------------------
    is_assign_ticket_number = False
    if auto_fill_ticket_number:
        for _ in range(3):
            is_assign_ticket_number = kktix_assign_ticket_number()
            if is_assign_ticket_number:
                break
            time.sleep(0.1)

        # When area include/exclude filter(s) are set and none match yet, refresh to wait for release.
        has_area_filter = (
            len(_parse_keywords(kktix_area_keyword)) > 0
            or len(_parse_keywords(kktix_area_exclude_keyword)) > 0
        )
        if not is_assign_ticket_number and has_area_filter:
            print("(with area filter) no matching KKTIX ticket available, refreshing...")
            try:
                time.sleep(0.3)
                driver.refresh()
            except Exception:
                pass
            return -1
    else:
        # Check if user manually selected a ticket quantity.
        for _, qty_input in available_rows:
            try:
                if _kktix_parse_positive_int(qty_input.get_attribute('value')) > 0:
                    is_assign_ticket_number = True
                    break
            except Exception:
                pass

    #---------------------------
    # part 4: human verification / CAPTCHA check (manual completion)
    #---------------------------
    has_verification, custom_input = kktix_has_human_verification()
    if has_verification:
        if custom_input is not None:
            try:
                current_val = custom_input.get_attribute('value') or ""
                already_focused = custom_input.get_attribute('data-bot-focused') == '1'
                if len(current_val) == 0 and not already_focused:
                    driver.execute_script(
                        "arguments[0].setAttribute('data-bot-focused', '1'); arguments[0].focus();",
                        custom_input,
                    )
            except Exception:
                pass
        # Pause auto-submit so the user can complete verification manually in the browser.
        return answer_index

    #---------------------------
    # part 5: press next step button
    #---------------------------
    if auto_press_next_step_button and is_assign_ticket_number:
        kktix_press_next_button()

    return answer_index


def fami_date_auto_select(url):
    date_list = None
    try:
        date_list = driver.find_elements(By.CSS_SELECTOR, '#game_page > table > tbody > tr:nth-child(4) > td > table > tbody > tr')
    except Exception as exc:
        #print("find #game_page date list fail")
        pass

    if date_list is not None:
        if len(date_keyword) == 0:
            el = None

            if date_auto_select_mode == CONST_FROM_TOP_TO_BOTTOM:

                row_index = 0
                for row in date_list:
                    row_index += 1

                    row_is_enabled=False
                    try:
                        row_is_enabled = row.is_enabled()
                    except Exception as exc:
                        pass

                    if row_is_enabled:
                        row_text = ""
                        try:
                            row_text = row.text
                        except Exception as exc:
                            #print("get text fail")
                            break

                        #print("date row_text:", row_index, row_text)
                        if len(row_text) > 0 and "/" in row_text:
                            try:
                                el = row.find_element(By.TAG_NAME, 'img')
                                if el is not None:
                                    #print("bingo, found first date button")
                                    break
                            except Exception as exc:
                                print("find date image button fail")
            else:
                # from bottom to top
                row_index = 0
                for row in reversed(date_list):
                    row_index += 1

                    row_is_enabled = False
                    try:
                        row_is_enabled = row.is_enabled()
                    except Exception as exc:
                        pass

                    if row_is_enabled:
                        row_text = ""
                        try:
                            row_text = row.text
                        except Exception as exc:
                            print("get text fail")
                            break

                        #print("date row_text:", row_index, row_text)
                        if len(row_text) > 0 and "/" in row_text:
                            try:
                                el = row.find_element(By.TAG_NAME, 'img')
                                if el is not None:
                                    break
                            except Exception as exc:
                                print("find date image button fail")

            if el is not None:
                # first date.
                try:
                    el.click()
                except Exception as exc:
                    #print("try to click date image button fail")
                    pass

        else:
        # match keyword.
            match_keyword_row = False

            row_index = 0
            for row in date_list:
                row_index += 1

                row_text = ""
                try:
                    row_text = row.text
                except Exception as exc:
                    print("get text fail")
                    break

                if len(row_text) > 0:
                    if date_keyword in row_text:
                        match_keyword_row = True

                        el = None
                        try:
                            el = row.find_element(By.TAG_NAME, 'img')
                        except Exception as exc:
                            print("find date image button fail")

                        if el is not None:
                            # first date.
                            try:
                                el.click()
                            except Exception as exc:
                                print("try to click date image button fail")

                    if match_keyword_row:
                        break

# purpose: area auto select
# return:
#   True: area block appear.
#   False: area block not appear.
# ps: return value for date auto select.
def fami_area_auto_select(url):
    ret = False
    areas = None

    area_list = None
    try:
        #print("try to find area block")
        my_css_selector = "#game_page > table > tbody > tr:nth-child(4) > td > table:nth-child(5) > tbody > tr > td:nth-child(1) > table > tbody > tr:nth-child(2) > td:nth-child(2) > table > tbody > tr:nth-child(2) > td > table > tbody > tr"
        area_list = driver.find_elements(By.CSS_SELECTOR, my_css_selector)
        if area_list is not None:
            if len(area_list) > 0:
                ret = True

                if len(area_keyword) == 0:
                    areas = area_list
                else:
                    # match keyword.
                    areas = []

                    row_index = 0
                    for row in area_list:
                        row_index += 1

                        row_is_enabled=False
                        try:
                            row_is_enabled = row.is_enabled()
                        except Exception as exc:
                            pass

                        if row_is_enabled:
                            row_text = ""
                            try:
                                row_text = row.text
                            except Exception as exc:
                                print("get text fail")
                                break

                            if len(row_text) > 0:
                                #print("area row_text:", row_index, row_text)
                                if area_keyword in row_text:
                                    areas.append(row)

    except Exception as exc:
        print("find #game_page date list fail")
        #print(exc)

    area = None
    if areas is not None:
        #print("area_auto_select_mode", area_auto_select_mode)
        #print("len(areas)", len(areas))
        if len(areas) > 0:
            target_row_index = 0

            if area_auto_select_mode == CONST_FROM_TOP_TO_BOTTOM:
                pass

            if area_auto_select_mode == CONST_FROM_BOTTOM_TO_TOP:
                target_row_index = len(areas)-1

            if area_auto_select_mode == CONST_RANDOM:
                target_row_index = random.randint(0,len(areas)-1)

            #print("target_row_index", target_row_index)
            area = areas[target_row_index]

    if area is not None:
        try:
            #print("area text", area.text)
            area.click()
        except Exception as exc:
            print("click area a link fail")
            print(exc)
            pass

    return ret

# purpose: ticket number auto select
# return:
#   True: ticket number block appear.
#   False: ticket number block not appear.
# ps: return value for area auto select.
def fami_ticket_number_auto_select(url):
    ret = False
    is_assign_ticket_number = False

    ticket_number_div = None
    try:
        ticket_number_div = driver.find_element(By.CSS_SELECTOR, '#Form_price > table > tbody > tr:nth-child(4) > td > table:nth-child(5) > tbody > tr:nth-child(2) > td > table > tbody > tr:nth-child(3) > td:nth-child(4) > span')
        if ticket_number_div is not None:
            el = None
            try:
                el = ticket_number_div.find_element(By.TAG_NAME, "select")
                if el is not None:
                    ret = True
                    #print("bingo, found ticket_number select")

                    ticket_number_select = Select(el)
                    if ticket_number_select is not None:
                        try:
                            #print("get select ticket value:" + Select(ticket_number_select).first_selected_option.text)
                            if ticket_number_select.first_selected_option.text=="0":
                                # target ticket number
                                ticket_number_select.select_by_visible_text(ticket_number)
                                is_assign_ticket_number = True
                        except Exception as exc:
                            #print("select_by_visible_text ticket_number fail")
                            #print(exc)
                            pass

                            try:
                                # try target ticket number twice
                                ticket_number_select.select_by_visible_text(ticket_number)
                                is_assign_ticket_number = True
                            except Exception as exc:
                                #print("select_by_visible_text ticket_number fail...2")
                                #print(exc)
                                pass

                                # try buy one ticket
                                try:
                                    ticket_number_select.select_by_visible_text("1")
                                    is_assign_ticket_number = True
                                except Exception as exc:
                                    print("select_by_visible_text 1 fail")
                                    pass

            except Exception as exc:
                #print("find ticket_number select fail")
                #print(exc)
                pass
    except Exception as exc:
        #print("find #Form_price ticket_number div fail")
        #print(exc)
        pass

    #print("is_assign_ticket_number", is_assign_ticket_number)
    time.sleep(0.3)

    wait = WebDriverWait(driver, 5)

    if is_assign_ticket_number:
        btn_auto_hyperlink_div = None
        try:
            btn_auto_hyperlink_div = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, '#chose_seat_btn_auto > a')))
            #btn_auto_hyperlink_div = driver.find_element(By.CSS_SELECTOR, '#chose_seat_btn_auto > a')
            if btn_auto_hyperlink_div is not None:
                btn_auto_hyperlink_div.click()
        except Exception as exc:
            print("find #chose_seat_btn_auto fail")
            print(exc)

    return ret

def fami_activity(url):
    #print("bingo")

    # Python 2 and 3
    try:
        # python3 urllib.parse:
        from urllib.parse import urlparse, parse_qs
    except ImportError:
        from urlparse import urlparse, parse_qs

    parsed_url = urlparse(url)
    qstr=parse_qs(parsed_url.query)
    code = None
    if 'code' in qstr:
        codes = qstr['code']
        if len(codes) > 0:
            code = codes[0]
        #print("qstr:", code)

    #---------------------------
    # part 1: press "buy" button.
    #---------------------------

    fami_start_to_buy_button = None
    try:
        fami_start_to_buy_button = driver.find_element(By.ID, 'under_img_order_buy')
        if fami_start_to_buy_button is not None:
            if True:
            #if fami_start_to_buy_button.is_displayed():
                if fami_start_to_buy_button.is_enabled():
                    #print('send click to buy button')


                    js = u'function testajax2(section_id,game_id,activitycode){ \
    $.ajax({ \
       type: "POST", \
       url: "FWT/FWT0000.aspx", \
       data: { \
            activitycode: activitycode, \
            game_id: game_id \
       }, \
       success: function(msg){ \
           var index=msg.indexOf("$(\'#img_order_buy\').click(function() {alert("); \
           if(index==-1) \
            $(\'#img_order_buy\').click(); \
           else \
            location.reload(); \
       } \
     }); \
} \
testajax2("","","' + code +'"); \
                    '
                    #print("execute js", js)

                    try:
                        driver.execute_script(js)
                        pass
                    except Exception as exc:
                        print("javascript Exception:")
                        print(exc)
                        pass

                    
                    #fami_start_to_buy_button.click()
                    pass
            else:
                print('unable to find buy button')
                pass
        else:
            #print("find under_img_order_buy button fail")
            pass
    except Exception as exc:
        #print("find under_img_order_buy button Exception")
        pass

    #---------------------------
    # part 4: auto fill ticket number
    #---------------------------

    ticket_number_div_exist = fami_ticket_number_auto_select(url)
    if ticket_number_div_exist:
        #print("ticket_number_div_exist appear")
        pass
    else:
        #---------------------------
        # part 3: auto press area
        #---------------------------
        if area_auto_select_enable:
            area_div_exist = fami_area_auto_select(url)
            if area_div_exist:
                #print("area appear")
                pass
            else:
                #---------------------------
                # part 2: auto press date
                #---------------------------
                if date_auto_select_enable:
                    fami_date_auto_select(url)


def urbtix_ticket_number_auto_select(url):
    ret = False
    is_assign_ticket_number = False

    try:
        el = driver.find_element(By.CSS_SELECTOR, 'select.chzn-select')
        if el is not None:
            ret = True
            #print("bingo, found ticket_number select")

            ticket_number_select = Select(el)
            if ticket_number_select is not None:
                try:
                    #print("get select ticket value:" + Select(ticket_number_select).first_selected_option.text)
                    if ticket_number_select.first_selected_option.text=="0":
                        # target ticket number
                        ticket_number_select.select_by_visible_text(ticket_number)
                        is_assign_ticket_number = True
                except Exception as exc:
                    print("select_by_visible_text ticket_number fail")
                    print(exc)

                    try:
                        # try target ticket number twice
                        ticket_number_select.select_by_visible_text(ticket_number)
                        is_assign_ticket_number = True
                    except Exception as exc:
                        print("select_by_visible_text ticket_number fail...2")
                        print(exc)

                        # try buy one ticket
                        try:
                            ticket_number_select.select_by_visible_text("1")
                            is_assign_ticket_number = True
                        except Exception as exc:
                            print("select_by_visible_text 1 fail")
                            pass

    except Exception as exc:
        print("find ticket_number select fail")
        print(exc)

    return ret, is_assign_ticket_number

# purpose: area auto select
# return:
#   True: area block appear.
#   False: area block not appear.
# ps: return value for date auto select.
def urbtix_area_auto_select(url):
    ret = False
    areas = None

    area_list = None
    try:
        #print("try to find urbtix area block")
        my_css_selector = "#ticket-price-tbl > tbody > tr"
        area_list = driver.find_elements(By.CSS_SELECTOR, my_css_selector)
        if area_list is not None:
            if len(area_list) > 0:
                ret = True

                if len(kktix_area_keyword) == 0:
                    areas = area_list
                else:
                    # match keyword.
                    areas = []

                    row_index = 0
                    for row in area_list:
                        row_index += 1
                        row_is_enabled=False
                        try:
                            row_is_enabled = row.is_enabled()
                        except Exception as exc:
                            pass

                        if row_is_enabled:
                            row_text = ""
                            try:
                                row_text = row.text
                            except Exception as exc:
                                print("get text fail")
                                break

                            if len(row_text) > 0:
                                #print("area row_text:", row_index, row_text)
                                if kktix_area_keyword in row_text:
                                    areas.append(row)

    except Exception as exc:
        print("find #ticket-price-tbl date list fail")
        print(exc)

    area = None
    if areas is not None:
        if len(areas) > 0:
            target_row_index = _select_target_index(len(areas), kktix_area_auto_select_mode)
            area = areas[target_row_index]

    if area is not None:
        el = None
        try:
            #print("area text", area.text)
            
            my_css_selector = "input.pricezone-radio-input"
            el = area.find_element(By.CSS_SELECTOR, my_css_selector)
            if el is not None:
                if el.is_enabled():
                    if not el.is_selected():
                        el.click()
                    ret = True
                    #print("bingo, click area radio")

        except Exception as exc:
            print("click area radio a link fail")
            print(exc)
            pass

    return ret

def urbtix_next_button_press(url):
    ret = False
    try:
        el = driver.find_element(By.CSS_SELECTOR, '#express-purchase-btn > div > span')
        if el is not None:
            ret = True
            print("bingo, found next button")

            if el.is_enabled():
                el.click()
                ret = True
    except Exception as exc:
        print("find next button fail")
        print(exc)

    return ret

def urbtix_performance(url):
    #print("urbtix bingo")

    if auto_fill_ticket_number:
        area_div_exist = False
        if len(kktix_area_keyword) > 0:
            area_div_exist = urbtix_area_auto_select(url)

    ticket_number_select_exist, is_assign_ticket_number = urbtix_ticket_number_auto_select(url)

    # todo.
    if auto_press_next_step_button:
        if is_assign_ticket_number:
            urbtix_next_button_press(url)

# purpose: area auto select
# return:
#   True: area block appear.
#   False: area block not appear.
# ps: return value for date auto select.
def cityline_area_auto_select(url):
    ret = False
    areas = None

    area_list = None
    try:
        #print("try to find cityline area block")
        # form[name="text"] > table:nth-child(12) > tbody > tr:nth-child(4) > td > table > tbody > tr > td:nth-child(1) > table > tbody > tr
        my_css_selector = "tr.menubar_text ~ tr"
        area_list = driver.find_elements(By.CSS_SELECTOR, my_css_selector)
        if area_list is not None:
            area_list_count = len(area_list)
            #print("area_list_count:", area_list_count)

            if area_list_count > 0:
                ret = True

                if len(kktix_area_keyword) == 0:
                    areas = area_list
                else:
                    # match keyword.
                    #print("start to match keyword:", kktix_area_keyword)
                    areas = []

                    row_index = 0
                    for row in area_list:
                        row_index += 1
                        row_is_enabled=False
                        try:
                            row_is_enabled = row.is_enabled()
                        except Exception as exc:
                            pass

                        if row_is_enabled:
                            row_text = ""
                            try:
                                row_text = row.text
                            except Exception as exc:
                                print("get text fail")
                                break

                            if len(row_text) > 0:
                                # for debug.
                                #print("area row_text:", row_index, row_text)
                                if kktix_area_keyword in row_text:
                                    areas.append(row)

                    #print("after match keyword, found count:", len(areas))
            else:
                print("not found area tr")
                pass
        else:
            print("area tr is None")
            pass

    except Exception as exc:
        print("find #ticket-price-tbl date list fail")
        print(exc)

    area = None
    if areas is not None:
        if len(areas) > 0:
            target_row_index = _select_target_index(len(areas), kktix_area_auto_select_mode)
            area = areas[target_row_index]

    if area is not None:
        el = None
        try:
            #print("area text", area.text)
            
            my_css_selector = "input[type=radio]"
            el = area.find_element(By.CSS_SELECTOR, my_css_selector)
            if el is not None:
                if el.is_enabled():
                    if not el.is_selected():
                        el.click()
                    ret = True
                    #print("bingo, click area radio")

        except Exception as exc:
            print("click area radio a link fail")
            print(exc)
            pass

    return ret

def cityline_area_selected_text(url):
    ret = None

    area_list = None
    try:
        #my_css_selector = "table.onePriceZoneInfoTable > tbody > tr"
        my_css_selector = "tr.menubar_text ~ tr"
        area_list = driver.find_elements(By.CSS_SELECTOR, my_css_selector)
        if area_list is not None:
            if len(area_list) > 0:
                row_index = 0
                for row in area_list:
                    row_index += 1
                    row_is_enabled=False
                    try:
                        row_is_enabled = row.is_enabled()
                    except Exception as exc:
                        pass

                    if row_is_enabled:
                        row_text = ""
                        try:
                            row_text = row.text
                        except Exception as exc:
                            print("get text fail")
                            break

                        if len(row_text) > 0:
                            el = None
                            try:
                                my_css_selector = "input[type=radio]"
                                el = row.find_element(By.CSS_SELECTOR, my_css_selector)
                                if el is not None:
                                    if el.is_enabled():
                                        if el.is_selected():
                                            ret = row_text
                                            break
                            except Exception as exc:
                                print(exc)
                                pass

    except Exception as exc:
        print(exc)
        pass
    return ret


def cityline_ticket_number_auto_select(url):
    ret = False
    is_assign_ticket_number = False
    selected_value = ""

    try:
        el = driver.find_element(By.CSS_SELECTOR, 'td.tix_type_select > div.chzn-container > a > span')
        if el is not None:
            if el.is_enabled():
                ret = True

                selected_value = el.text
                #print("selected_value:", selected_value)

                if selected_value == "0":
                    el.click()
                    time.sleep(0.3)

                is_options_enabled = False

                el_options = driver.find_element(By.CSS_SELECTOR, 'td.tix_type_select > div.chzn-container > div.chzn-drop')
                if el_options is not None:
                    if el_options.is_enabled():
                        is_options_enabled = True

                #print("is_options_enabled:", is_options_enabled)
                if is_options_enabled:
                    el_options_li = driver.find_elements(By.CSS_SELECTOR, 'td.tix_type_select > div.chzn-container > div.chzn-drop > ul > li')
                    if el_options_li is not None:
                        if len(el_options_li) > 0:
                            for row in el_options_li:
                                if row is not None:
                                    if row.is_enabled():
                                        row_text = row.text
                                        if not row_text is None:
                                            if row_text == ticket_number:
                                                print("row_text clicked:", row_text)
                                                row.click()
                                                is_assign_ticket_number = True
                                                break
    except Exception as exc:
        #print("find ticket_number select fail")
        #print(exc)
        pass

    return ret, is_assign_ticket_number


def cityline_next_button_press(url):
    ret = False
    try:
        time.sleep(0.2)
        el = driver.find_element(By.CSS_SELECTOR, '#expressPurchaseButton')
        if el is not None:
            ret = True
            print("bingo, found next button")

            if el.is_enabled():
                el.click()
                ret = True
    except Exception as exc:
        print("find next button fail")
        print(exc)

    return ret

def cityline_event(url):
    ret = False

    is_non_member_displayed = False

    try:
        el_non_member = driver.find_element(By.ID, 'buyBtWalkIn')
        if el_non_member is not None:
            if el_non_member.is_enabled():
                #if el_non_member.is_displayed():
                is_non_member_displayed = True
    except Exception as exc:
        #print(exc)
        pass

    try:
        el = driver.find_element(By.ID, 'buyBt')
        if el is not None:
            if el.is_enabled():
                #if el.is_displayed():
                    # for non-member
                    #javascript:selectPerformance(1);
                    # for member
                    #javascript:selectPerformance(0);

                if not is_non_member_displayed:
                    # when two buttons appear, do nothing.
                    el.click()
    except Exception as exc:
        #print("find next button fail")
        #print(exc)
        pass

    return ret

def cityline_captcha_auto_focus(url):
    ret = False
    try:
        el = driver.find_element(By.CSS_SELECTOR, 'input[name=verify]')
        if el is not None:
            if el.is_enabled():
                inputed_text = el.get_attribute('value')
                if not inputed_text is None:
                    if len(inputed_text) == 0:
                        #print("click the input text")
                        el.click()
                        ret = True
            else:
                #print("element is not enable")
                pass
        else:
            print("element is None")
    except Exception as exc:
        print("find verify text fail")
        print(exc)
        pass

    # make captcha image bigger/
    if ret:
        try:
            el = driver.find_element(By.CSS_SELECTOR, '#captchaImage')
            if el is not None:
                if el.is_enabled():
                    image_width = el.get_attribute('width')
                    #print("image_width:", image_width)
                    if image_width != 200:
                        driver.execute_script("document.getElementById(\"captchaImage\").width=200;")
        except Exception as exc:
            print("excute script resize fail")
            print(exc)
            pass

    return ret


def cityline_performance(url):
    #print("cityline bingo")
    if "performance.do;" in url:
        cityline_captcha_auto_focus(url)

    if "?cid=" in url:
        if auto_fill_ticket_number:
            area_div_exist = False
            if len(kktix_area_keyword) > 0:
                area_div_exist = cityline_area_auto_select(url)

        ticket_number_select_exist, is_assign_ticket_number = cityline_ticket_number_auto_select(url)

        # todo.
        if auto_press_next_step_button:
            if is_assign_ticket_number:
                selected_text = cityline_area_selected_text(url)
                if not selected_text is None:
                    if kktix_area_keyword in selected_text:
                        # must same with our settting to auto press.
                        for i in range(3):
                            click_ret = cityline_next_button_press(url)
                            if click_ret:
                                break


def facebook_login(url):
    ret = False
    try:
        el = driver.find_element(By.CSS_SELECTOR, '#email')
        if el is not None:
            ret = True
            if el.is_enabled():
                inputed_text = el.get_attribute('value')
                if len(inputed_text) == 0:
                    el.send_keys(facebook_account)
                    ret = True
    except Exception as exc:
        #print("find #email fail")
        #print(exc)
        pass

    return ret


def _is_driver_closed_error(exc):
    msg = (str(exc) or repr(exc)).lower()
    closed_markers = (
        'chrome not reachable',
        'invalid session id',
        'disconnected',
        'not connected to devtools',
        'failed to decode response from marionette',
        'browsing context has been discarded',
        'target window already closed',
    )
    return any(marker in msg for marker in closed_markers)


def _is_blank_page(current_url):
    if current_url is None:
        return True
    return str(current_url).strip().lower() in ("", "about:blank", "data:,")


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


def is_cloudflare_challenge_page(url=None):
    if url and '/cdn-cgi/challenge-platform' in url:
        return True

    if driver is None:
        return False

    try:
        title = (driver.title or '').strip().lower()
        cf_titles = (
            'just a moment',
            'attention required! | cloudflare',
            'checking your browser',
            '請稍候',
        )
        if any(marker in title for marker in cf_titles):
            return True
    except Exception:
        pass

    cf_selectors = (
        '#challenge-form',
        '#challenge-running',
        '#cf-challenge-running',
        '.cf-turnstile',
        'iframe[src*="challenges.cloudflare.com"]',
    )
    for selector in cf_selectors:
        try:
            elements = driver.find_elements(By.CSS_SELECTOR, selector)
            for el in elements:
                if el.is_displayed():
                    return True
        except Exception:
            pass

    return False


def main():
    global driver

    if load_config() is None:
        sys.exit(1)

    try:
        driver = create_driver(browser)
        if browser_debug_address:
            # 附加到已開啟的 Chrome：保留使用者已手動開好（含登入/已通過 Cloudflare）的頁面，
            # 只有當目前是空白頁時才去開啟 homepage。
            print("Attached to existing browser at %s" % browser_debug_address)
            open_homepage = True
            try:
                if not _is_blank_page(driver.current_url):
                    open_homepage = False
            except Exception:
                pass
            if open_homepage:
                driver.get(homepage)
        else:
            driver.get(homepage)
    except Exception as exc:
        logger.error("Failed to initialize WebDriver: %s", exc, exc_info=True)
        if (getattr(sys, "frozen", False) or "__compiled__" in globals()) and sys.stdin and sys.stdin.isatty():
            try:
                input("\nPress Enter to close...")
            except EOFError:
                pass
        sys.exit(1)

    # internal variable. 說明：這是一個內部變數，請略過。
    url = ""
    last_url = ""
    # for tixcraft
    is_verifyCode_editing = False
    # for kktix
    answer_index = -1
    was_paused = False
    was_cf_paused = False

    try:
        while True:
            time.sleep(0.1)

            if is_bot_paused():
                if not was_paused:
                    print("Bot paused (manual control). Click Resume to continue.")
                    was_paused = True
                time.sleep(0.2)
                continue
            elif was_paused:
                print("Bot resumed.")
                was_paused = False

            is_alert_popup = False

            # https://stackoverflow.com/questions/57481723/is-there-a-change-in-the-handling-of-unhandled-alert-in-chromedriver-and-chrome
            default_close_alert_text = [
            ]
            try:
                alert = None
                if driver is not None:
                    alert = driver.switch_to.alert
                if alert is not None:
                    if alert.text is not None:
                        is_match_auto_close_text = False
                        for txt in default_close_alert_text:
                            if len(txt) > 0:
                                if txt in alert.text:
                                    is_match_auto_close_text = True
                        #print("alert3 text:", alert.text)

                        if is_match_auto_close_text:
                            alert.accept()
                            print("alert3 accepted")

                        is_alert_popup = True
                else:
                    print("alert3 not detected")
            except NoAlertPresentException:
                pass
            except NoSuchWindowException:
                try:
                    window_handles = driver.window_handles
                    if len(window_handles) >= 1:
                        driver.switch_to.window(window_handles[0])
                    else:
                        print(u'quit bot')
                        break
                except Exception:
                    print(u'quit bot')
                    break
            except Exception as exc:
                if _is_driver_closed_error(exc):
                    print(u'quit bot')
                    break
                logger.error('Exception2 for alert')
                logger.error(exc, exc_info=True)

            #MUST "do nothing: if alert popup.
            #print("is_alert_popup:", is_alert_popup)
            if is_alert_popup:
                continue

            url = ""
            try:
                url = driver.current_url
            except NoSuchWindowException:
                try:
                    window_handles = driver.window_handles
                    if len(window_handles) >= 1:
                        driver.switch_to.window(window_handles[0])
                    else:
                        print(u'quit bot')
                        break
                except Exception:
                    print(u'quit bot')
                    break
            except UnexpectedAlertPresentException:
                is_pass_alert = False
                if last_url == "":
                    is_pass_alert = True

                # for tixcraft verify
                if u'tixcraft' in last_url and u'/verify/' in last_url:
                    is_pass_alert = True

                if is_pass_alert:
                    try:
                        driver.switch_to.alert.accept()
                    except NoAlertPresentException:
                        pass
            except Exception as exc:
                if _is_driver_closed_error(exc):
                    print(u'quit bot')
                    break
                logger.error(exc, exc_info=True)

            if url is None or len(url) == 0:
                continue

            # 說明：輸出目前網址，覺得吵的話，請註解掉這行。
            if url != last_url:
                print(url)
            last_url = url

            if is_cloudflare_challenge_page(url):
                if not was_cf_paused:
                    print("Cloudflare verification detected; pausing automation for manual completion...")
                    was_cf_paused = True
                time.sleep(0.5)
                continue
            elif was_cf_paused:
                print("Cloudflare verification cleared; resuming automation.")
                was_cf_paused = False

            if 'tixcraft.com' in url:
                if '/ticket/order' in url:
                    # do nothing.
                    continue

                if '/ticket/payment' in url:
                    # do nothing.
                    continue

                if tixcraft_redirect(url):
                    continue

                if date_auto_select_enable:
                    date_auto_select(url)

                # choose area
                if area_auto_select_enable:
                    area_auto_select(url)

                if '/ticket/verify/' in url:
                    tixcraft_verify(url)

                # main app, to select ticket number.
                if '/ticket/ticket/' in url:
                    is_verifyCode_editing = tixcraft_ticket_main(url, is_verifyCode_editing)
                else:
                    # not is input verify code, reset flag.
                    is_verifyCode_editing = False

            # for kktix.cc and kktix.com
            if 'kktix.c' in url:
                if '/registrations/new' in url:
                    answer_index = kktix_reg_new(url, answer_index)
                elif '/registrations/' in url:
                    # Step-2 page (fill registration info / confirm order). URL is
                    # /registrations/<order_id>; auto-check agreement controls.
                    answer_index = kktix_registration_form(url, answer_index)
                else:
                    answer_index = -1
                    if '/events/' in url and '/registrations' not in url:
                        kktix_event_redirect(url)

            # for famiticket
            if 'famiticket.com' in url:
                if 'activity_info.aspx' in url:
                    fami_activity(url)

            # for urbtix
            # https://ticket.urbtix.hk/internet/secure/event/37348/performanceDetail
            if 'urbtix.hk' in url:
                # http://msg.urbtix.hk
                if 'msg.urbtix.hk' in url:
                    # delay to avoid ip block.
                    time.sleep(1.1)
                    driver.get('http://www.urbtix.hk/')
                # http://busy.urbtix.hk
                if 'busy.urbtix.hk' in url:
                    # delay to avoid ip block.
                    time.sleep(1.1)
                    driver.get('http://www.urbtix.hk/')

                if '/performanceDetail/' in url:
                    urbtix_performance(url)

            if 'cityline.com' in url:
                if '/event.do' in url:
                    cityline_event(url)

                if '/Events.do' in url:
                    if len(driver.window_handles) == 2:
                        try:
                            driver.close()
                        except Exception:
                            pass

                if '/performance.do' in url:
                    cityline_performance(url)
    except KeyboardInterrupt:
        print("Stopped by user.")
    finally:
        if driver is not None:
            try:
                driver.quit()
            except Exception:
                pass


if __name__ == "__main__":
    main()