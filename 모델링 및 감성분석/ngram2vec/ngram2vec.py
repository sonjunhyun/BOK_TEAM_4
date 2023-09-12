import pandas as pd
import numpy as np
from tqdm import tqdm
import re

class NGram2VecGenerator:
    def __init__(self, filepath):
        self.df = pd.read_csv(filepath, index_col=0)
        self.clean_text()
        self.token2idx_fast = {}
        self.idx2token_fast = {}

    def clean_text(self):
        # 텍스트 내의 따옴표 제거
        self.df['text'] = self.df['text'].str.replace("'", "")
        self.df['text'] = self.df['text'].str.replace('"', "")

    @staticmethod
    def extract_tuples(s):
        # 텍스트에서 튜플 형태의 문자열을 추출
        return [tuple(map(str.strip, match.split(','))) for match in re.findall(r'\(([^)]+)\)', s)]

    def generate_ngrams(self, n):
        # n-gram 생성
        return [[tokens[i:i+n] for i in range(len(tokens)-n+1)] for tokens in self.df['text'].apply(self.extract_tuples)]

    def add_ngram_columns(self, max_n=5):
        # n-gram 컬럼 추가
        for n in range(1, max_n+1):
            col_name = f"TOKEN_{n}"
            self.df[col_name] = self.generate_ngrams(n)

    def compile_tokens(self):
        # 전체 토큰을 컴파일하고 고유한 토큰의 인덱스를 만듦
        tokens_list = [np.concatenate(self.df[col].values).tolist() for col in [x for x in self.df.columns if x.startswith('TOKEN_')]]
        tokens_flat = [" ".join(map(str, x)) for sublist in tokens_list for x in sublist]
        unique_tokens_series = pd.Series(tokens_flat).drop_duplicates().reset_index(drop=True)
        self.token2idx_fast = {token: idx for idx, token in unique_tokens_series.items()}
        self.idx2token_fast = {idx: token for token, idx in self.token2idx_fast.items()}

    def merge_ngram_columns(self):
        # 모든 n-gram 컬럼을 하나로 합침
        self.df['TOKENS_TOTAL'] = ""
        for i in range(1, 6):
            self.df['TOKENS_TOTAL'] += self.df[f'TOKEN_{i}'].map(lambda x: "#".join([" ".join(map(str, token)) for token in x])) + "#"
            self.df['TOKENS_TOTAL'] = self.df['TOKENS_TOTAL'].str.replace("(", "[").str.replace(")", "]")
        self.df['TOKENS_TOTAL_IDX'] = self.df['TOKENS_TOTAL'].map(lambda x: [self.token2idx_fast[token] for token in x[:-1].split("#") if token in self.token2idx_fast])

    def generate_ngram2vec(self):
        # ngram2vec 생성
        ngram2vec = []
        for idx_list in tqdm(self.df['TOKENS_TOTAL_IDX'], desc="ngram2vec 진행중"):
            arr_tem = [0] * len(self.token2idx_fast)
            for idx in set(idx_list):
                arr_tem[idx] = 1
            ngram2vec.append(arr_tem)
        return np.array(ngram2vec)

    def process(self):
        # 전체 프로세스 실행
        self.add_ngram_columns()
        self.compile_tokens()
        self.merge_ngram_columns()
        return self.generate_ngram2vec()

if __name__ == "__main__":
    generator = NGram2VecGenerator('./tokenize_text_withoutnews.csv')
    ngram2vec_array = generator.process()
