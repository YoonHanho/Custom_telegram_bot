#!/usr/bin/python3

from urllib.request import urlopen
from bs4 import BeautifulSoup


address = {'Daum': 'http://www.daum.net/',
           'Naver': 'http://www.naver.com/'}
query_address = {'Daum': 'http://search.daum.net/search?w=tot&q=',
                 'Naver': 'https://search.naver.com/search.naver?query='}


def get_rank_string(portal_site):
    try:
        page_src = urlopen(address[portal_site])
        bsObj = BeautifulSoup(page_src.read(), "lxml")
    except (HTTPError, AttributeError) as e:
        return None

    try:
        if (portal_site == 'Daum'):
            # searching_word = bsObj.find("ol",{"id":"realTimeSearchWord"}).li.div.div.find("span",{"class":"txt_issue"}).a.strong.get_text()
            # 2017.04.08
            searching_word = bsObj.find("ol", {"class": "list_hotissue"}).li.div.div.find("span", {
                "class": "txt_issue"}).a.get_text()
        elif (portal_site == 'Naver'):
            # searching_word = bsObj.find("ol",{"id":"realrank"}).li.a.span.get_text()
            # 2017.04.08
            searching_word = bsObj.find("ul", {"class": "ah_l"}).li.find("span", {"class": "ah_k"}).get_text()
        else:
            return None
    except AttributeError as e:
        return None

    return searching_word


if __name__ == '__main__':

    for portal_site in ['Daum', 'Naver']:
        real_rank_item = get_rank_string(portal_site)

        if real_rank_item is not None:
            print(portal_site + '\t: ' + real_rank_item)
        else:
            print(portal_site + "\t: Error")