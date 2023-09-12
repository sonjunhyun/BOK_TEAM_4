import re
from tika import parser
import os
from os import listdir
from os.path import isfile, join
import pandas as pd
from datetime import datetime

# hwp 파일 텍스트로 변환
def convert_hwp_to_text(source_folder, output_folder):
    # 지정 폴더 내 파일 목록 조회 (파일만)
    hwp_files = [f for f in listdir(source_folder) if isfile(join(source_folder, f))]
    
    result = []
    for hwp in hwp_files:
        time = re.search(r'\((.*?)\)', hwp).group(1)
        hwp_filepath = os.path.join(source_folder, hwp)
        
        # hwp 파일 텍스트로 변환
        parsedText = parser.from_file(hwp_filepath)["content"]
        new_dict = {
            'time': time,
            'text': parsedText
        }
        result.append(new_dict)

    df = pd.DataFrame(result)
    output_path = os.path.join(output_folder, '금통위의사록(텍스트파일).xlsx')

    # DataFrame을 Excel 파일로 저장
    df.to_excel(output_path, index=False)

# 텍스트 전처리 함수
def text_filtering(text):
    text = re.sub(r'(\n{2,}|- \d+ -|―|｢|｣|[․/→←+]|^.*hwp*\w*[A-Za-z])', '', text)
    text = re.sub(r'\s+', ' ', text)
    text = text.split('6. 회의경과')[1]
    return text

# 메인 함수
def main():
    source_folder = "../data/hwp/"
    output_folder = "../data/"
    
    # hwp 파일을 텍스트로 변환하여 Excel로 저장
    convert_hwp_to_text(source_folder, output_folder)

    # Excel 파일 읽어오기
    minutes = pd.read_excel(os.path.join(output_folder, '금통위의사록(텍스트파일).xlsx'), usecols=[1, 2])
    minutes['time'] = minutes['time'].astype(str)

    # 날짜 추출 및 datetime으로 변환
    date_list = []
    for time in minutes['time']:
        date_list.extend(re.findall(r'\d{4}.\d{1,2}.\d{1,2}', time))
    minutes['time'] = date_list
    minutes['time'] = pd.to_datetime(minutes['time'], format='%Y.%m.%d')

    # 연도가 2009~2021년인 의사록 필터링
    minutes = minutes[(minutes['time'].dt.year >= 2009) & (minutes['time'].dt.year <= 2021)]
    minutes.sort_values(by='time')

    # 텍스트 전처리 적용
    minutes['text'] = minutes['text'].apply(text_filtering)

    # 결과를 csv 파일로 저장
    minutes.to_csv('의사록_hwp2text_전처리(완).csv', encoding='utf-8-sig', index=False)

if __name__ == "__main__":
    main()