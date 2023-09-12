import pandas as pd
import re

# csv 파일 읽기
def read_csv_file(file_path):
    df = pd.read_csv(file_path, index_col=0)
    return df

# 문장 분할을 위한 패턴 리스트
def get_split_patterns():
    patterns = [
        r'(?<=[함])[ \s\n\.;\(]',
        r'(?<=[음])[ \s\n\.;\(]',
        r'(?<=[됨])[ \s\n\.;\(]',
        r'(?<=[임])[ \s\n\.;\(]',
        r'(?<=[봄])[ \s\n\.;\(]',
        r'(?<=[짐])[ \s\n\.;\(]',
        r'(?<=[움])[ \s\n\.;\(]',
        r'(?<=[었음])[ \s\n\.;\(]',
        r'(?<=[였음])[ \s\n\.;\(]',
        r'(?<=[하였음])[ \s\n\.;\(]',
        r'(?<=다) '
    ]
    return patterns

# 문장 분할 함수
def split_text(text, patterns):
    split_texts = [text]
    for pattern in patterns:
        split_texts = [segment for text in split_texts for segment in re.split(pattern, text)]
    return split_texts

# 주어진 데이터프레임을 텍스트 분할하여 새로운 데이터프레임 생성
def split_and_create_dataframe(df, patterns):
    split_df = df['text'].apply(split_text, patterns=patterns)
    split_df = split_df.explode().reset_index(drop=True).rename(columns={'text': 'split_text'})
    result_df = pd.concat([df[['time']], split_df], axis=1)
    return result_df

# 주어진 데이터프레임에서 길이가 20 이상인 텍스트만 남기는 함수
def filter_text_by_length(df, min_length=20):
    filtered_df = df[df['split_text'].str.len() >= min_length]
    return filtered_df

# 결과를 csv 파일로 저장하는 함수
def save_to_csv(df, output_file):
    df.to_csv(output_file, index=False)

# 메인 함수
def main():
    input_file = './의사록_hwp2text_전처리(완).csv'
    output_file = './minutes_sen.csv'

    # csv 파일 읽기
    df = read_csv_file(input_file)

    # 텍스트 분할을 위한 패턴 리스트 가져오기
    patterns = get_split_patterns()

    # 텍스트 분할 및 새로운 데이터프레임 생성
    split_df = split_and_create_dataframe(df, patterns)

    # 길이가 20 이상인 텍스트만 필터링
    filtered_df = filter_text_by_length(split_df)

    # 결과를 csv 파일로 저장
    save_to_csv(filtered_df, output_file)

if __name__ == "__main__":
    main()
