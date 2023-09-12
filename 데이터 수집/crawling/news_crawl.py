import scrapy
from datetime import datetime, timedelta
from user_agent import generate_user_agent
from urllib.parse import urljoin
from .clean import *

'''
#파일 위치
finance > spiders> news_crawl.py

#가상환경 생성
python = 3.8 버전으로 가상환경 생성

#스크래피 설치
conda install -c scrapinghub scrapy

#필요 라이브러리 설치
pip install hanja
pip install chardet
pip install user_agent

#날짜 변경 _ 각자 본인이 맡은 연도로 수정
start_date = date(2009, 1, 1)
end_date = date(2009, 12, 31)

#스크래피 실행 및 파일 저장(cmd 창에 입력)
scrapy crawl finance -o '파일명'.csv -t csv
'''

headers = {'User-Agent': generate_user_agent(os='win', device_type='desktop')}

class NaverFinanceNewsSpider(scrapy.Spider):
    name = 'finance'
    allowed_domains = ['finance.naver.com']
    def __init__(self, *args, **kwargs):
        super(NaverFinanceNewsSpider, self).__init__(*args, **kwargs)
        self.base_url = 'https://finance.naver.com/news/news_search.naver?rcdate=&q=%B1%DD%B8%AE&x=0&y=0&sm=all.basic&pd=4&stDateStart={}&stDateEnd={}&page={}'
        self.current_date = datetime(2009, 1, 1)
        self.end_date = datetime(2009, 1, 27)
        self.current_page = 1

    def start_requests(self):
        #크롤링 시작 url 생성
        date_str = self.current_date.strftime('%Y-%m-%d')
        url = self.base_url.format(date_str, date_str, self.current_page)
        yield scrapy.Request(url=url, callback=self.parse, headers=headers)

    def parse(self, response):
        # 기사 목록이 없을 경우 다음 날짜로 넘어감
        if not response.css('#contentarea_left > div.newsSchResult > dl > dt.articleSubject'):
            self.current_date += timedelta(days=1)
            #다음 날짜가 종료 날짜 이전일 경우 다시 parse함수 실행
            if self.current_date <= self.end_date:
                self.current_page = 1
                date_str = self.current_date.strftime('%Y-%m-%d')
                url = self.base_url.format(date_str, date_str, self.current_page)
                yield scrapy.Request(url=url, callback=self.parse, headers=headers)
            return

        # 기사 목록이 있을 경우 기사 url 크롤링 진행
        detail_urls = response.css('#contentarea_left > div.newsSchResult > dl > dd.articleSubject a::attr(href), dt.articleSubject a::attr(href)').getall()
        for detail_url in detail_urls:
            try:
                absolute_url = urljoin('https://finance.naver.com', detail_url)
                yield scrapy.Request(url=absolute_url, callback=self.parse_detail, headers=headers)
            except Exception as e:
                print(e)
                continue

        # 다음 페이지로 넘어감
        self.current_page += 1
        date_str = self.current_date.strftime('%Y-%m-%d')
        next_url = self.base_url.format(date_str, date_str, self.current_page)
        yield scrapy.Request(url=next_url, callback=self.parse, headers=headers)

    #상세 뉴스 페이지 내용 크롤링(제목, 날짜, 본문, 신문사)
    def parse_detail(self, response):
        title = response.xpath('//*[@id="contentarea_left"]/div[2]/div[1]/div[2]/h3/text()').get()
        date = response.xpath('//*[@id="contentarea_left"]/div[2]/div[1]/div[2]/div/span/text()').get()
        company = response.xpath('//*[@id="contentarea_left"]/div[2]/div[1]/div[1]/span/img/@alt').get()

        #본문 p태그 유무에 따라 크롤링
        content_texts = response.xpath('//*[@id="content"]/p/text()').getall()
        contents = content_texts if content_texts else response.xpath('//*[@id="content"]/text()').getall()

        cleaned_title = clean_title(title)
        cleaned_date = clean_date(date)
        cleaned_contents = ' '.join(clean_content(c) for c in contents)
        cleaned_company = clean_company(company)

        yield {
            'date': cleaned_date,
            'title': cleaned_title,
            'company': cleaned_company,
            'contents': cleaned_contents
        }

    


        
