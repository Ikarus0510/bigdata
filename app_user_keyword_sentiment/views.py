from django.http import JsonResponse
from django.shortcuts import render
import pandas as pd
from django.views.decorators.csrf import csrf_exempt
from app_news_multiangle.views import convert_chinese_date
from datetime import timedelta


def home(request):
    return render(request, 'app_user_keyword_sentiment/home.html')

def load_df_data():
    global df
    df = pd.read_csv('app_user_keyword_sentiment/dataset/yahoo_news_sentiment.csv', sep='|')
    df['date'] = df['date'].apply(convert_chinese_date)


# 啟動時呼叫
load_df_data()


def filter_df_by_keywords(df, keywords, cond, cate, weeks):
    end_date = df['date'].max()
    start_date = end_date - timedelta(weeks=weeks)

    # 篩選時間
    df_filtered = df[(df['date'] >= start_date) & (df['date'] <= end_date)]

    # 篩選類別
    if cate != '全部':
        df_filtered = df_filtered[df_filtered['category'] == cate]

    # 篩選關鍵字
    if cond == 'and':
        for kw in keywords:
            df_filtered = df_filtered[df_filtered['content'].str.contains(kw)]
    elif cond == 'or':
        df_filtered = df_filtered[df_filtered['content'].apply(lambda x: any(kw in x for kw in keywords))]

    return df_filtered


@csrf_exempt
def api_get_userkey_sentiment(request):
    userkey = request.POST.get('userkey')
    cate = request.POST.get('cate')
    cond = request.POST.get('cond')
    weeks = int(request.POST.get('weeks'))

    query_keywords = userkey.split()
    df_query = filter_df_by_keywords(df, query_keywords, cond, cate, weeks)


    if len(df_query) == 0:
        return JsonResponse({'error': 'No results found for the given keywords.'})

    
    sentiCount, sentiPercnt = get_article_sentiment(df_query)

    if weeks <= 4:
        freq_type = 'D'
    else:
        freq_type = 'W'

    line_data_pos = get_daily_basis_sentiment_count(df_query, sentiment_type='pos', freq_type=freq_type)
    line_data_neg = get_daily_basis_sentiment_count(df_query, sentiment_type='neg', freq_type=freq_type)

    response = {
        'sentiCount': sentiCount,
        'data_pos': line_data_pos,
        'data_neg': line_data_neg,
    }

    return JsonResponse(response)


def get_article_sentiment(df_query):

    sentiCount = {'Positive': 0, 'Negative': 0, 'Neutral': 0}
    sentiPercnt = {'Positive': 0, 'Negative': 0, 'Neutral': 0}
    numberOfArticle = len(df_query)

    for senti in df_query.sentiment:
        
        if float(senti) >= 0.6:
            sentiCount['Positive'] += 1
        elif float(senti) <= 0.4:
            sentiCount['Negative'] += 1
        else:
            sentiCount['Neutral'] += 1


    for polar in sentiCount:
        try:
            sentiPercnt[polar] = int(sentiCount[polar] / numberOfArticle * 100)
        except:
            sentiPercnt[polar] = 0

    return sentiCount, sentiPercnt

def get_daily_basis_sentiment_count(df_query, sentiment_type='pos', freq_type='D'):
    
    if sentiment_type == 'pos':
        lambda_function = lambda senti: 1 if senti >= 0.6 else 0
    elif sentiment_type == 'neg':
        lambda_function = lambda senti: 1 if senti <= 0.4 else 0
    else:
        return None


    freq_df = pd.DataFrame({
        'date_index': pd.to_datetime(df_query.date),
        'frequency': [lambda_function(senti) for senti in df_query.sentiment]
    })


    freq_df_group = freq_df.groupby(pd.Grouper(key='date_index', freq=freq_type)).sum()

    freq_df_group.reset_index(inplace=True)


    xy_line_data = [{'x': date.strftime('%Y-%m-%d'), 'y': freq}
                    for date, freq in zip(freq_df_group.date_index, freq_df_group.frequency)]

    return xy_line_data

print("app_user_keyword_sentiment loaded successfully!")
