import pandas as pd
import ast

class ToneAnalyzer:
    def __init__(self, pol_score_df_path, minuets_ngram_path):
        self.n2vdic = pd.read_csv(pol_score_df_path)
        self.data = pd.read_csv(minuets_ngram_path, encoding='utf-8')
        self.epsilon = 1e-10
        self.new_dic = self.prepare_dictionary()

    def prepare_dictionary(self):
        self.n2vdic.drop(columns='Polarity_Score', inplace=True)
        self.n2vdic['Token'] = self.n2vdic['Token'].str.replace('[', '(')
        self.n2vdic['Token'] = self.n2vdic['Token'].str.replace(']', '), ')
        self.n2vdic['Token'] = self.n2vdic['Token'].str[:-2]
        self.n2vdic = self.n2vdic[self.n2vdic['Sentiment'] != '중립']
        self.n2vdic['Sentiment'] = self.n2vdic['Sentiment'].str.replace('상승', 'hawkish')
        self.n2vdic['Sentiment'] = self.n2vdic['Sentiment'].str.replace('하락', 'dovish')
        return dict(zip(self.n2vdic['Token'], self.n2vdic['Sentiment']))

    def count_tags(self, row):
        hawkish_count = 0
        dovish_count = 0

        # 문자열로 저장된 튜플 리스트를 실제 리스트로 변환
        tuples = ast.literal_eval(row['ngram'])

        for t in tuples:
            tag = self.new_dic.get(str(t))
            if tag == 'hawkish':
                hawkish_count += 1
            elif tag == 'dovish':
                dovish_count += 1

        return pd.Series([hawkish_count, dovish_count])

    def analyze_tone(self):
        self.data[['hawkish_count', 'dovish_count']] = self.data.apply(self.count_tags, axis=1)
        self.data['tone_s'] = (self.data['hawkish_count'] - self.data['dovish_count']) / (self.data['hawkish_count'] + self.data['dovish_count'] + self.epsilon)
        self.data['tone_label'] = self.data['tone_s'].apply(lambda x: 'newtral' if x == 0 else 'hawkish' if x > 0 else 'dovish')
        hawkish_counts = self.data.groupby('time').apply(lambda x: (x['tone_label'] == 'hawkish').sum())
        dovish_counts = self.data.groupby('time').apply(lambda x: (x['tone_label'] == 'dovish').sum())

        result = self.data.drop_duplicates(subset='time').set_index('time')
        result['hawkish_count'] = hawkish_counts
        result['dovish_count'] = dovish_counts
        result = result.reset_index()
        result['doc_tone'] = (result['hawkish_count'] - result['dovish_count']) / (result['hawkish_count'] + result['dovish_count'] + self.epsilon)

        return result

    def save_result(self, output_path='./tone_by_n2v.csv'):
        result = self.analyze_tone()
        result.to_csv(output_path, index=False)


analyzer = ToneAnalyzer(pol_score_df_path='./pol_score_df.csv', minuets_ngram_path='./minuets_ngram.csv')
analyzer.save_result()
