import pandas as pd
import re

def load_data(path):
    return pd.read_csv(path)

def common_preprocessing(df):
    df.dropna(inplace=True)
    df.columns = ['증권사', '날짜', '텍스트']
    
    for split_text in ['본 자료는', '본  자료는', '동 자료는', '동  자료는',
                       '본 자료에', '본  자료에', '동 자료에', '동  자료에',
                       '본  조사자료', '본  조사분석자료']:
        df['텍스트'] = df['텍스트'].str.split(split_text).str[0]
    
    return df

def remove_brackets_content(df):
    def remove_brackets(text, pattern):
        return re.sub(pattern, '', text)
    
    df['텍스트'] = df['텍스트'].apply(lambda x: remove_brackets(x, r'\[.*?\]'))
    df['텍스트'] = df['텍스트'].apply(lambda x: remove_brackets(x, r'\(.*?\)'))
    df['텍스트'] = df['텍스트'].apply(lambda x: remove_brackets(x, r'\<.*?\>'))

    return df

def specific_preprocessing(df):
    df.drop(df[df['증권사'] == '다올투자증권'].index, inplace=True)
    df.drop(df[df['텍스트'] == "No /Root object! - Is this really a PDF?"].index, inplace=True)
    
    # 같은 단어가 4번 반복되는 패턴을 찾아서 지우기
    def remove_repeated_words(text):
        return re.sub(r'(\w+)(\1{3,})', r'\1', text)
    
    df['텍스트'] = df['텍스트'].apply(remove_repeated_words)

    for split_text in ['이 자료에 게재된 내용들은 본인의 의견을 정확하게 반영하고 있으며 외부의 부당한 압력이나 간섭 없이 작성되었음을 확인함.',
                       '이 페이지는 편집상 공백입니다.', '자료 발간일 현재 본 자료를', '이 자료에 게재된', '본 조사분석자료는']:
        df['텍스트'] = df['텍스트'].str.split(split_text).str[0]
    
    
    mask = df['증권사'] == '키움증권'
    df.loc[mask, '텍스트'] = df.loc[mask, '텍스트'].str.split('Compliance Notice').str[0]
    df.drop(df[df['증권사'] == '하나증권'].index, inplace=True)
    df.drop(df[(df['증권사']=='유안타증권') & (df['텍스트'].str.startswith('(단위: 억원, %)'))].index, inplace=True)
    df.drop(df[(df['증권사']=='교보증권') & (df['텍스트'].str.startswith('Daily'))].index, inplace=True)

    return df

def filter_hangul(df):
    df = df[df['텍스트'].apply(lambda x: bool(re.search('[ㄱ-힣]', x)))]
    return df

if __name__ == "__main__":
    DATA_PATH = '/content/drive/Shareddrives/4조/data/bondreport/final/bond_report_concat.csv'
    df = load_data(DATA_PATH)
    df = common_preprocessing(df)
    df = remove_brackets_content(df)
    df = specific_preprocessing(df)
    df = filter_hangul(df)
