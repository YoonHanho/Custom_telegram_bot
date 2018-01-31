#!/usr/bin/python3

from selenium import webdriver
from selenium.webdriver.support.ui import Select
from bs4 import BeautifulSoup
import re
from collections import OrderedDict

def get_apt_notification():
    driver = webdriver.PhantomJS(service_args=['--load-images=no'])
    driver.get('https://www.apt2you.com/houseSaleSimpleInfo.do')
    select = Select(driver.find_element_by_id('home_sel'))
    select.select_by_value('house_03')
    element1 = driver.find_element_by_id("leaseGubunAll")
    element1.click()
    element2 = driver.find_element_by_id("leaseGubun0")
    element2.click()
    element2 = driver.find_element_by_class_name("btn_blue")
    element2.click()
    driver.implicitly_wait(10)

    # driver.save_screenshot('test.png')
    bsObj = BeautifulSoup(driver.page_source, "lxml")
    table = bsObj.find("div", {"class": "table_type1"})
    head = table.thead.findAll("th",{"scope":"col"})
    theadList = []
    for headitem in head:
        theadList.append(headitem)
    rows = table.tbody.findAll("tr")
    apartmentList = []
    for contentsList in rows:
        item = OrderedDict()
        contents = contentsList.findAll("td")

        for thead, content in zip(theadList, contents):
            content_text = content.get_text().replace('\n', ' ').replace('\r', ' ')
            content_text = re.sub(r'\s+', ' ', content_text)
            content_text = content_text.strip()
            thead_text = thead.get_text().strip()
            if thead_text != "" and content_text != "":
                item[thead_text] = content_text
        apartmentList.append(item)

    return apartmentList

if __name__ == '__main__':
    apartmentList = get_apt_notification()
    for item in apartmentList:
        for key in item.keys():
            print(key + ' : ' + item[key])
        print()