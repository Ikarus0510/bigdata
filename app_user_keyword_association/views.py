from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse

from datetime import datetime, timedelta
import pandas as pd
import math
import re
from collections import Counter

# ✅ 處理中文時間格式：2025年4月14日 下午1:04
def parse_chinese_datetime(s):
    if isinstance(s, datetime):  # ✅ 如果已經是 datetime，就直接回傳
        return s
    try:
        return datetime.strptime(s, "%Y年%m月%d日 下午%I:%M")
    except ValueError:
        try:
            return datetime.strptime(s, "%Y年%m月%d日 上午%I:%M")
        except:
            return pd.NaT

# (1) we can load data using read_csv() 自己app的csv檔案
# global variable
# df = pd.read_csv('dataset/cna_news_200_preprocessed.csv', sep='|')

# (2) we can load data using reload_df_data() function 隔壁app的csv檔案
# global variable
def load_df_data_v1():
    global df
    df = pd.read_csv('app_user_keyword/dataset/yahoo_news_preprocessed.csv', sep='|')
    df['date'] = df['date'].apply(parse_chinese_datetime)  # ✅ 轉換成 datetime

# (4) df can be import from app_user_keyword 隔壁app的變數
import app_user_keyword.views as userkeyword_views
def load_df_data():
    global df
    df = userkeyword_views.df
    df['date'] = df['date'].apply(parse_chinese_datetime)  # ✅ 轉換成 datetime

load_df_data()

def home(request):
    return render(request, 'app_user_keyword_association/home.html')

@csrf_exempt
def api_get_userkey_associate(request):
    userkey = request.POST.get('userkey')
    cate = request.POST['cate']
    cond = request.POST.get('cond')
    weeks = int(request.POST.get('weeks'))
    key = userkey.split()

    df_query = filter_dataFrame_fullText(key, cond, cate, weeks)
    print(key)
    print(len(df_query))

    if len(df_query) != 0:
        newslinks = get_title_link_topk(df_query, k=15)
        related_words, clouddata = get_related_word_clouddata(df_query)
        same_paragraph = get_same_para(df_query, key, cond, k=10)
    else:
        newslinks = []
        related_words = []
        same_paragraph = []
        clouddata = []

    response = {
        'newslinks': newslinks,
        'related_words': related_words,
        'same_paragraph': same_paragraph,
        'clouddata': clouddata,
        'num_articles': len(df_query),
    }
    return JsonResponse(response)

def filter_dataFrame_fullText(user_keywords, cond, cate, weeks):
    # 🔧 確保 date 欄位是 datetime
    df['date'] = pd.to_datetime(df['date'], errors='coerce')

    # 🔄 計算日期範圍
    end_date = df['date'].max().date()
    start_date = end_date - timedelta(weeks=weeks)

    period_condition = (df['date'].dt.date >= start_date) & (df['date'].dt.date <= end_date)

    if cate == "全部":
        condition = period_condition
    else:
        condition = period_condition & (df.category == cate)

    if cond == 'and':
        condition = condition & df.content.apply(lambda text: all(qk in text for qk in user_keywords))
    elif cond == 'or':
        condition = condition & df.content.apply(lambda text: any(qk in text for qk in user_keywords))

    df_query = df[condition]
    return df_query

def get_title_link_topk(df_query, k=25):
    items = []
    for i in range(len(df_query[0:k])):
        category = df_query.iloc[i]['category']
        title = df_query.iloc[i]['title']
        link = df_query.iloc[i]['link']
        photo_link = df_query.iloc[i]['photo_link']
        if pd.isna(photo_link):
            photo_link = ''
        item_info = {
            'category': category,
            'title': title,
            'link': link,
            'photo_link': photo_link
        }
        items.append(item_info)
    return items

def get_related_word_clouddata(df_query):
    counter = Counter()
    for idx in range(len(df_query)):
        pair_dict = dict(eval(df_query.iloc[idx].top_key_freq))
        counter += Counter(pair_dict)
    wf_pairs = counter.most_common(20)

    min_ = wf_pairs[-1][1]
    max_ = wf_pairs[0][1]
    textSizeMin = 20
    textSizeMax = 120
    clouddata = [{'text': w, 'size': int(textSizeMin + (f - min_) / (max_ - min_) * (textSizeMax - textSizeMin))}
                 for w, f in wf_pairs]

    return wf_pairs, clouddata

def cut_paragraph(text):
    paragraphs = text.split('。')
    paragraphs = list(filter(None, paragraphs))
    return paragraphs

def get_same_para(df_query, user_keywords, cond, k=30):
    same_para = []
    for text in df_query.content:
        paragraphs = cut_paragraph(text)
        for para in paragraphs:
            para += "。"
            if cond == 'and':
                if all(re.search(kw, para) for kw in user_keywords):
                    same_para.append(para)
            elif cond == 'or':
                if any(re.search(kw, para) for kw in user_keywords):
                    same_para.append(para)
    return same_para[0:k]

print("app_user_keyword_association was loaded!")
