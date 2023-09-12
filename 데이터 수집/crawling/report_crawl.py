import os
import pandas as pd
import requests
from bs4 import BeautifulSoup
from urllib import request
from pdfminer.converter import TextConverter
from pdfminer.layout import LAParams
from pdfminer.pdfpage import PDFPage
from io import StringIO
import re

SAVE_DIR = '/content/drive/Shareddrives/4조/data/bondreport/'
CSV_DIR = f'{SAVE_DIR}final/'
BASE_URL = 'https://finance.naver.com/research/debenture_list.nhn'

def get_soup(url, params=None):
    # 주어진 URL로부터 BeautifulSoup 객체를 반환
    resp = requests.get(url, params=params)
    return BeautifulSoup(resp.content, 'html.parser')

def download_reports(total_page=191):
    # 보고서 다운로드 및 정보 추출 함수
    all_td_link, all_td_date, all_tr_comp = [], [], []

    # 각 페이지에서 필요한 정보들을 추출
    for page in range(1, total_page + 1):
        soup = get_soup(BASE_URL, params={'page': page})
        all_td_link.extend(soup.select('table.type_1 td.file'))
        all_td_date.extend([td.text for idx, td in enumerate(soup.select('table.type_1 td.date')) if idx % 2 == 0])
        all_tr_comp.extend([tr.find_all('td')[1].text for tr in soup.select('table.type_1 tr') if tr.find_all('td')])

    # 보고서 다운로드
    fail_list = []
    for idx, td in enumerate(all_td_link):
        fname = f'{(idx // 30) + 1}_{(idx % 30) + 1}.pdf'
        save_path = os.path.join(SAVE_DIR, fname)
        try:
            file_link = td.find('a')['href']
            request.urlretrieve(file_link, save_path)
        except:
            fail_list.append(fname)
            with open(save_path, 'wb') as f:
                pass

    return all_tr_comp, all_td_date, fail_list

def pdf_to_text(fname):
    # PDF 파일을 텍스트로 변환하는 함수
    rsrcmgr = PDFResourceManager()
    retstr = StringIO()
    codec = 'utf-8'
    laparams = LAParams()
    device = TextConverter(rsrcmgr, retstr, codec=codec, laparams=laparams)
    with open(os.path.join(SAVE_DIR, fname), 'rb') as fp:
        interpreter = PDFPageInterpreter(rsrcmgr, device)
        for page in PDFPage.get_pages(fp, set(), password='', caching=True, check_extractable=True):
            interpreter.process_page(page)

        text = retstr.getvalue()
        cleaned_lines = [line for line in text.split('\n') if not re.fullmatch(r"[0-9\s,.\-%$]+", line.strip())]
        return '\n'.join(cleaned_lines)

def save_to_csv(comp_list, date_list):
    # 데이터를 CSV로 저장하는 함수
    text_list = [pdf_to_text(f'{(idx // 30) + 1}_{(idx % 30) + 1}.pdf') for idx in range(len(comp_list))]
    df = pd.DataFrame({
        '증권사': comp_list,
        '날짜': date_list,
        '텍스트': text_list
    })
    for page in range(1, (len(comp_list) // 30) + 2):
        df.iloc[(page-1)*30:page*30].to_csv(os.path.join(CSV_DIR, f'bond_report page_{page}.csv'), index=False)

def merge_csv_files(total_page=191):
    # 모든 CSV 파일을 하나로 합치는 함수
    dfs = [pd.read_csv(os.path.join(CSV_DIR, f'bond_report page_{i}.csv'), index_col=0) for i in range(1, total_page+1)]
    final_df = pd.concat(dfs)
    final_df.to_csv(os.path.join(CSV_DIR, 'bond_report_concat.csv'), index=False)

if __name__ == "__main__":
    comp_list, date_list, fail_list = download_reports()
    save_to_csv(comp_list, date_list)
    merge_csv_files()
