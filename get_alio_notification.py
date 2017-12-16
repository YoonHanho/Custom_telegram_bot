#!/usr/bin/python3

from urllib.request import urlopen
import ssl
import re
from bs4 import BeautifulSoup


def get_alio_notification():
    ssl._create_default_https_context = ssl._create_unverified_context
    page_src = \
        urlopen(
            'http://job.alio.go.kr/recruit.do?'
            + 'pageNo=1&param=&idx=&recruitYear=&recruitMonth='
            + '&detail_code=R600019&detail_code=R600020&location=R3010&location=R3017'
            + '&work_type=R1010&career=R2020&replacement=N&s_date=&e_date=&org_name=&ing=2&title=&order=TERM_END'
        )
    bsObj = BeautifulSoup(page_src.read(), "lxml")

    theadList = []
    for headitem in bsObj.find("table", {"class": "tbl type_03"}).thead.findAll("th",{"scope": "col"}):
        theadList.append(headitem)

    job_list = []

    for contentsList in bsObj.find("table", {"class": "tbl type_03"}).tbody.findAll("tr"):
        item = {}
        contents = contentsList.findAll("td")

        for thead, content in zip(theadList, contents):
            content_text = content.get_text().replace('\n', ' ').replace('\r', ' ')
            content_text = re.sub(r'\s+', ' ', content_text)
            content_text = content_text.strip()
            thead_text = thead.get_text().strip()
            if thead_text != "" and content_text != "":
                item[thead_text] = content_text
        job_list.append(item)

    job_list = sorted(job_list, key=lambda k: k['번호'])

    return job_list


if __name__ == '__main__':
    lists = get_alio_notification()

    for item in lists:
        for key in item.keys():
            print(key + ' : ' + item[key])
        print()
