import pandas as pd
import numpy as np
from tqdm import tqdm

class SOPMIGenerator:
    def __init__(self, df, token2idx, ngram2vec):
        self.df = df
        self.token2idx = token2idx
        self.ngram2vec = ngram2vec
        self.pol_score_df = pd.DataFrame()
        seed_hk_refined = [
    [('높', 'VA')], [('팽창', 'NNG')], [('인상', 'NNG')], [('매파', 'NNG')], [('성장', 'NNG')],
    [('투기', 'NNG'), ('억제', 'NNG')], [('상승', 'NNG')], [('인플레이션', 'NNG'), ('압력', 'NNG')],
    [('증가', 'NNG')], [('위험', 'NNG'), ('선호', 'NNG')], [('상회', 'NNG')], [('물가', 'NNG'), ('상승', 'NNG')],
    [('과열', 'NNG')], [('금리', 'NNG'), ('상승', 'NNG')], [('확장', 'NNG')], [('상방', 'NNG'), ('압력', 'NNG')],
    [('긴축', 'NNG')], [('변동성', 'NNG'), ('감소', 'NNG')], [('흑자', 'NNG')], [('채권', 'NNG'), ('가격', 'NNG')],
    [('하락', 'NNG')], [('견조', 'NNG')], [('요금', 'NNG'), ('인상', 'NNG')], [('낙관', 'NNG')], [('부동산', 'NNG'), ('가격', 'NNG')],
    [('상승', 'NNG')], [('상향', 'NNG')]]

        seed_dv_refined = [
    [('낮', 'VA')], [('축소', 'NNG')], [('인하', 'NNG')], [('비둘기', 'NNG')], [('둔화', 'NNG')],
    [('악화', 'NNG')], [('하락', 'NNG')], [('회복', 'NNG'), ('못하', 'VX')], [('감소', 'NNG')],
    [('위험', 'NNG'), ('회피', 'NNG')], [('하회', 'NNG')], [('물가', 'NNG'), ('하락', 'NNG')],
    [('위축', 'NNG')], [('금리', 'NNG'), ('하락', 'NNG')], [('침체', 'NNG')], [('하방', 'NNG'), ('압력', 'NNG')],
    [('완화', 'NNG')], [('변동성', 'NNG'), ('확대', 'NNG')], [('적자', 'NNG')], [('채권', 'NNG'), ('가격', 'NNG')],
    [('상승', 'NNG')], [('부진', 'NNG')], [('요금', 'NNG'), ('인하', 'NNG')], [('비관', 'NNG')], [('부동산', 'NNG'), ('가격', 'NNG')],
    [('하락', 'NNG')], [('하향', 'NNG')]]
    
    # seed 리스트를 토큰 형식에 맞게 변환
    def refine_seeds(self, seed_list):
        # 토큰 형식에 맞게 변환
        refined_seeds = [" ".join(["/".join(token) for token in tokens]) for tokens in seed_list]
        # 대괄호로 변환
        refined_seeds = [token.replace("(", "[").replace(")", "]") for token in refined_seeds]
        return refined_seeds

    def token_probability(self):
        # 각 토큰별 등장 확률 구하기
        num_total = len(self.df)
        token_prob = [sum(self.ngram2vec[:, i]) / num_total for i in tqdm(range(len(self.token2idx.keys())), desc="각 토큰별 등장 확률 구하기")]
        return token_prob

    def generate_seed_idx(self, seed_list):
        # 보유 토큰 안에 있는 시드 워드만 남기기
        seed_idx = [self.token2idx[x] for x in seed_list if x in self.token2idx.keys()]
        return seed_idx

    def sopmi_calculation(self, seed_hk_idx, seed_dv_idx, token_prob):
        # numpy 연산을 활용하여 SO-PMI 계산 최적화하기
        num_iterations = 50
        seed_hk_probs = [token_prob[idx] for idx in seed_hk_idx]
        seed_dv_probs = [token_prob[idx] for idx in seed_dv_idx]

        accumulated_pol_scores = np.zeros(len(self.token2idx))
        epsilon = 1e-10
        for _ in tqdm(range(num_iterations)):
            # 각 반복마다 seed_hk_idx와 seed_dv_idx에서 무작위로 10개의 인덱스를 선택
            seed_hk_idx_10 = np.random.choice(seed_hk_idx, 10, replace=False)
            seed_dv_idx_10 = np.random.choice(seed_dv_idx, 10, replace=False)

            sopmi_hk, sopmi_dv = [], []

            for tk_idx in range(len(self.token2idx)):
                tk_prob = token_prob[tk_idx]

                # numpy 연산을 활용하여 매파성 단어들의 공동출현 확률 계산
                inter_prob_hk = np.mean(np.any(self.ngram2vec[:, seed_hk_idx_10] & self.ngram2vec[:, tk_idx][:, None], axis=1))
                sopmi_hk_tem = np.log10((inter_prob_hk + epsilon) / ((tk_prob * np.mean(seed_hk_probs)) + epsilon))
                sopmi_hk.append(sopmi_hk_tem)

                # numpy 연산을 활용하여 비둘기파성 단어들의 공동출현 확률 계산
                inter_prob_dv = np.mean(np.any(self.ngram2vec[:, seed_dv_idx_10] & self.ngram2vec[:, tk_idx][:, None], axis=1))
                sopmi_dv_tem = np.log10((inter_prob_dv + epsilon) / ((tk_prob * np.mean(seed_dv_probs)) + epsilon))
                sopmi_dv.append(sopmi_dv_tem)

            # 해당 반복의 극성 점수를 계산하고 누적
            sopmi_hk, sopmi_dv = np.array(sopmi_hk), np.array(sopmi_dv)
            accumulated_pol_scores += (sopmi_hk - sopmi_dv)

        # 모든 반복 후 평균 극성 점수 계산
        average_pol_score = accumulated_pol_scores / num_iterations
        return average_pol_score

    def classify_sentiment(self, score, threshold_positive, threshold_negative):
        # 극성 점수에 따른 감정 구분
        if score > threshold_positive:
            return "상승"
        elif score < threshold_negative:
            return "하락"
        else:
            return "중립"

    def process(self, threshold_positive=1.1, threshold_negative=-1.1):
        seed_hk = self.refine_seeds(self.seed_hk_refined)
        seed_dv = self.refine_seeds(self.seed_dv_refined)
        
        token_prob = self.token_probability()
        seed_hk_idx = self.generate_seed_idx(seed_hk)
        seed_dv_idx = self.generate_seed_idx(seed_dv)
        pol_scores = self.sopmi_calculation(seed_hk_idx, seed_dv_idx, token_prob)

        self.pol_score_df = pd.DataFrame({
            'Token': list(self.token2idx.keys()),
            'Polarity_Score': pol_scores
        })

        self.pol_score_df['Sentiment'] = self.pol_score_df['Polarity_Score'].apply(lambda score: self.classify_sentiment(score, threshold_positive, threshold_negative))
        return self.pol_score_df

    def save_to_csv(self, filename):
        self.pol_score_df.to_csv(filename, index=False)
