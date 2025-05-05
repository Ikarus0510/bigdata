from django.http import JsonResponse
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt
import pandas as pd
import numpy as np

# 要追蹤的政治人物
target_people = ['李孝亮', '吳思瑤', '吳沛憶']

def load_data():
    df = pd.read_csv('app_taipei_recall/dataset/yahoo_news_sentiment_cleaned.csv', sep='|')

    def find_person(row):
        for person in target_people:
            if pd.notna(row['entities']) and person in row['entities']:
                return person
            if pd.notna(row['title']) and person in row['title']:
                return person
            if pd.notna(row['content']) and person in row['content']:
                return person
        return None

    df['person'] = df.apply(find_person, axis=1)
    df = df[df['person'].notna()]
    return df

# 讀取資料
df_news = load_data()

def home(request):
    return render(request, 'app_taipei_recall/home.html')

@csrf_exempt
def api_get_taipei_recall_data(request):
    list_pkNames = []
    list_total_articles = []
    list_total_frequency = []
    list_sentiInfo = []
    list_freq_news_category = []
    list_freq_daily_line_chart = []

    # 額外加上照片連結 & 顏色
    list_photos = [
        '/static/img/李孝亮.jpg',
        '/static/img/吳思瑤.jpg',
        '/static/img/吳沛憶.jpg'
    ]
    list_colors = [
        'rgba(255, 99, 132, 0.5)',
        'rgba(54, 162, 235, 0.5)',
        'rgba(255, 206, 86, 0.5)'
    ]

    list_category = ['政治', '社會地方']

    for person in target_people:
        df_person = df_news[df_news['person'] == person]

        list_pkNames.append(person)

        total = len(df_person)
        list_total_articles.append(total)
        list_total_frequency.append(total)  # 目前曝光次數 = 總篇數

        # 情緒統計
        pos_count = (df_person['sentiment'] == '正面').sum()
        neg_count = (df_person['sentiment'] == '負面').sum()
        if total > 0:
            pos_rate = round(pos_count / total * 100, 2)
            neg_rate = round(neg_count / total * 100, 2)
            neut_rate = round(100 - pos_rate - neg_rate, 2)
        else:
            pos_rate = neut_rate = neg_rate = 0
        list_sentiInfo.append([pos_rate, neut_rate, neg_rate])

        # 新聞分類次數
        freq_by_category = []
        for cat in list_category:
            count = (df_person['category'] == cat).sum()
            freq_by_category.append(int(count))
        list_freq_news_category.append(freq_by_category)

        # 每日新聞量
        daily_counts = df_person.groupby('date').size().reset_index(name='counts')
        daily_list = []
        for _, row in daily_counts.iterrows():
            daily_list.append({
                'x': row['date'],
                'y': int(row['counts'])
            })
        list_freq_daily_line_chart.append(daily_list)

    result = {
        'list_pkNames': list_pkNames,
        'list_total_articles': list_total_articles,
        'list_total_frequency': list_total_frequency,
        'list_sentiInfo': list_sentiInfo,
        'list_freq_news_category': list_freq_news_category,
        'list_category': list_category,
        'list_freq_daily_line_chart': list_freq_daily_line_chart,
        'list_photos': list_photos,
        'list_colors': list_colors,
    }

    return JsonResponse(result)

print('Load app taipei recall...')
