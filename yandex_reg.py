import argparse
import logging
import os
import time
import requests
from captcha_solver import CaptchaSolver
from settings import read_settings
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.remote.command import Command
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.common.proxy import *
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
from fake_useragent import UserAgent

__version__ = "0.0.1.dev0"
logger = logging.getLogger(__name__)
DEFAULT_CONFIG_NAME = "config"


def parse_arguments():
    parser = argparse.ArgumentParser(
        description='Yandex mail registration with selenium web driver',
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    parser.add_argument('-V', '--verbose', action='store_const',
                        const=logging.DEBUG, dest='verbosity',
                        help='Make a lot of noise')

    parser.add_argument('-v', '--version', action='version',
                        version=__version__,
                        help='Print version number and exit')

    parser.add_argument('-c', '--config', dest='config', default=DEFAULT_CONFIG_NAME,
                        help='Config file with login and lastname. Default'
                             'value is {0}'.format(DEFAULT_CONFIG_NAME))

    return parser.parse_args()


def captcha_solve(url, key):
    if key is not None:
        try:
            solver = CaptchaSolver('antigate', api_key=key)
            raw_data = requests.get(url, stream=True).raw.read()
            key = solver.solve_captcha(raw_data)
            return key
        except Exception as e:
            print("Exception: ", e)
    return None


def ya_reg_selenium(browser, settings):
    # browser.set_page_load_timeout(30)
    # browser.implicitly_wait(30);

    browser.get('https://mail.yandex.ru/')
    # browser.maximize_window()
    time.sleep(5)
    create_element = browser.find_element_by_css_selector(
        "a[class='button2 button2_size_mail-big button2_theme_mail-action button2_type_link HeadBanner-Button with-shadow']")
    create_element.click()

    time.sleep(1)
    lang = browser.find_element_by_css_selector("span[class='link__inner']")
    lang.click()
    lang = browser.find_element_by_css_selector("span[class='menu__text']")
    lang.click()

    time.sleep(4)

    # firstname = browser.find_element_by_id('firstname')
    # firstname.click()
    # firstname.clear()
    browser.switch_to.active_element.send_keys(settings['FIRSTNAME'])
    browser.switch_to.active_element.send_keys(Keys.TAB)

    time.sleep(1)
    browser.switch_to.active_element.send_keys(settings['LASTNAME'])

    browser.switch_to.active_element.send_keys(Keys.TAB)
    time.sleep(1)
    browser.switch_to.active_element.send_keys(settings['LOGIN'])
    time.sleep(1)
    browser.switch_to.active_element.click()

    browser.switch_to.active_element.send_keys(Keys.TAB)
    time.sleep(1)
    browser.switch_to.active_element.send_keys(settings['PASSWORD'])

    browser.switch_to.active_element.send_keys(Keys.TAB)
    time.sleep(1)
    browser.switch_to.active_element.send_keys(settings['PASSWORD'])

    no_number = browser.find_element_by_css_selector("span[class='toggle-link link_has-no-phone']")
    no_number.click()
    time.sleep(1)
    browser.switch_to.active_element.send_keys(Keys.TAB)
    time.sleep(1)
    browser.switch_to.active_element.send_keys(Keys.TAB)
    time.sleep(1)
    browser.switch_to.active_element.send_keys(settings['ANSWER'])
    time.sleep(1)
    browser.switch_to.active_element.send_keys(Keys.TAB)
    time.sleep(10)
    captcha = browser.find_element_by_css_selector("div[class='captcha__container']")
    image = captcha.find_element_by_tag_name("img")
    img_src = image.get_attribute("src")
    print(img_src)
    cs = captcha_solve(img_src, settings['ANTIGATE_KEY'])
    print(cs)
    time.sleep(1)
    browser.switch_to.active_element.send_keys(cs)

    register = browser.find_element_by_css_selector(
        "button[class='button2 button2_size_l button2_theme_action button2_width_max button2_type_submit js-submit']")
    register.click()

    time.sleep(10)

    # browser.get('https://music.yandex.ru/artist/6265372')

    try:
        wait = browser.WebDriverWait(browser, 10)
    except:
        time.sleep(10)
        for i in range(0, 15):
            browser.switch_to.active_element.send_keys(Keys.TAB)
        time.sleep(1)
        browser.switch_to.active_element.send_keys(Keys.ENTER);
        time.sleep(15)
        browser.switch_to.active_element.send_keys(Keys.TAB)
        time.sleep(1)
        browser.switch_to.active_element.send_keys(Keys.ENTER);
    # play = browser.find_element_by_css_selector("button[class='button2 button2_rounded button-play button-play__type_album local-icon-theme-white page-album__play button2_w-icon']")
    # play.click()


def main():
    args = parse_arguments()

    logger.addHandler(logging.StreamHandler())

    if (args.verbosity):
        logger.setLevel(args.verbosity)
    else:
        logger.setLevel(logging.INFO)
    logger.debug('yandex_reg version: %s', __version__)

    if args.config is not None:
        config_dir = args.config
        settings = read_settings(config_dir)

        browsers = {}
        cnt = 0
        ua = UserAgent()

        with open("proxy.txt", "r") as f:
            for line in f:
                user_agent = ua.random
                print(line, user_agent)

                URL = 'http://httpbin.org/ip'

                if cnt in browsers:
                    print("QUIT")
                    browsers[cnt].quit()

                proxyDict = {"http": "http://" + line.strip(), "https": "https://" + line.strip()}
                try:
                    r = requests.get(URL, proxies=proxyDict)
                    print(r.status_code)
                except Exception as e:
                    print("Proxy error")
                    continue

                chrome_options = webdriver.ChromeOptions()
                # chrome_options.add_argument('--proxy-server=%s' % line)
                # chrome_options.add_argument("user-agent=" + user_agent)
                # chrome_options.add_argument('--headless')
                browsers[cnt] = webdriver.Chrome(chrome_options=chrome_options)
                ya_reg_selenium(browsers[cnt], settings)
                cnt = cnt + 1

                if cnt == 1:
                    time.sleep(200)
                    cnt = 0


if __name__ == "__main__":
    main()
