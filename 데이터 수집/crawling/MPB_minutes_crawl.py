import requests
from bs4 import BeautifulSoup
import os
import pandas as pd
import re
from tika import parser
from os import listdir
from os.path import isfile, join

# 저장 위치 설정
SAVE_DB_DIR = "../data/hwp"
if not os.path.exists(SAVE_DB_DIR):
    os.makedirs(SAVE_DB_DIR)

# 전체 페이지 수 반환
def get_total_pages(url):
    resp = requests.get(url)
    soup = BeautifulSoup(resp.content)
    end_page = int(soup.select('.i.end > a')[-1].attrs['href'].split('=')[-1])
    return end_page

# 페이지 내 데이터 크롤링
def crawl_page(url, page):
    params = {
        'pageIndex': page
    }
    resp = requests.get(url, params=params)
    soup = BeautifulSoup(resp.content)
    li_list = soup.select('.bdLine.type2 > ul > li')
    return li_list

# hwp 파일 다운로드
def download_hwp_files(li_list, save_dir):
    for li_item in li_list:
        link_li = li_item.select('.fileGoupBox ul li')
        for link in link_li:
            if link.select_one('a').attrs['title'][-3:] == 'hwp':
                link_url = link.select_one('a').attrs['href']
                title = li_item.select_one('.row span a span span').text
                download_url = 'http://www.bok.or.kr' + link_url
                file_res = requests.get(download_url)
                file_name = '{}.hwp'.format(title)
                file_path = os.path.join(save_dir, file_name)
                with open(file_path, 'wb') as f:
                    f.write(file_res.content)

# 메인 함수
def main():
    url = 'http://www.bok.or.kr/portal/bbs/B0000245/list.do?menuNo=200761'
    end_page = get_total_pages(url)
    print('총 {}페이지 까지 크롤링을 시작합니다.'.format(end_page))
    
    li_list = []
    for i in range(1, end_page + 1):
        li_list.extend(crawl_page(url, i))
        print(f"페이지 {i} 크롤링 성공")

    download_hwp_files(li_list, SAVE_DB_DIR)

if __name__ == "__main__":
    main()