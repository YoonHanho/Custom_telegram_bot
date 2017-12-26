#!/usr/bin/python3

import validators
from bs4 import BeautifulSoup
from urllib.request import (urlopen, HTTPError)
from selenium import webdriver
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.by import By
import re
from selenium.common.exceptions import TimeoutException
import collections


def get_author(bsObj):
    try:
        authorObj = bsObj.find("meta", {"name": "author"})
    except AttributeError:
        return None

    return authorObj['content']


def get_title(bsObj):
    try:
        titleObj = bsObj.find("meta", {"itemprop": "name"})
    except AttributeError:
        return None

    return titleObj['content']


def get_subtitle(bsObj):
    try:
        subtitleObj = bsObj.findAll("div", {"class":" Grid Grid--with-gutter d:f@md p-b:4 "})
    except AttributeError:
        return None

    subtitle_list = {}
    for each_line in subtitleObj:
        time_button = each_line.find("button", {"class":" sb a-i:c b-r:.1 bg:gray-ll c:gray-d d:f f:.9 h:3 m-t:.5 p-x:.4 p-y:.1 t-d:n "})
        time_step = time_button.findAll("div")[1].get_text()
        sentenceObj = each_line.findAll("a", {"class":"t-d:n hover/bg:gray-l.5"})

        string = ''

        for each_sentence in sentenceObj:
            part_string = each_sentence.get_text()
            part_string = part_string.strip()
            part_string = re.sub(r'\n', ' ', part_string)
            part_string = re.sub(r'\r', ' ', part_string)
            string = string + ' ' + part_string

        subtitle_list[time_step] = string

    return subtitle_list


def get_subtitle_from_TED(web_address):
    if validators.url(web_address):
        try:
            driver = webdriver.PhantomJS(service_args=['--load-images=no'])
            driver.get(web_address)
        except HTTPError:
            print("The server don't respond.")
    else:
        print("This is not a web address.")
        return None

    try:
        WebDriverWait(driver, 20).until(
            EC.presence_of_element_located(
                (By.XPATH, "//div[@class=' Grid Grid--with-gutter d:f@md p-b:4 ']")
            )
        )
    except TimeoutException:
        print(driver.current_url)
        return None

    bsObj = BeautifulSoup(driver.page_source, "lxml")

    TED_subtitle = {}
    TED_subtitle['title'] = get_title(bsObj)
    TED_subtitle['author'] = get_author(bsObj)
    TED_subtitle['subtitle'] = get_subtitle(bsObj)

    if TED_subtitle['title'] == None or TED_subtitle['title'] == None or TED_subtitle['title'] == None:
        return None
    else:
        return TED_subtitle


def main():
    subtitle = get_subtitle_from_TED('https://www.ted.com/talks/ken_robinson_says_schools_kill_creativity/transcript?language=en')

    subtitle = collections.OrderedDict(sorted(subtitle.items()))

    if subtitle:
        print('Title : ' + subtitle['title'])
        print('Author : ' + subtitle['author'])

        for time_step in subtitle['subtitle'].keys():
            string = time_step
            string = string + " : "
            string = string + subtitle['subtitle'][time_step]
            print(string)


if __name__ == '__main__':
    main()
