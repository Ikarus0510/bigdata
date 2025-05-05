import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import re
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
from django.shortcuts import render

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.cluster import AgglomerativeClustering

from collections import Counter


# 中文日期格式轉換
def convert_chinese_date(date_str):
    try:
        if date_str == '無時間' or pd.isna(date_str):
            return pd.NaT
        match = re.match(r"(\d{4})年(\d{1,2})月(\d{1,2})日 (上午|下午)(\d{1,2}):(\d{2})", date_str)  #2025年4月14日 週一 下午1:04
        if not match:
            return pd.NaT
        year, month, day, ampm, hour, minute = match.groups()
        hour = int(hour)
        if ampm == '下午' and hour != 12:
            hour += 12
        elif ampm == '上午' and hour == 12:
            hour = 0
        return datetime(int(year), int(month), int(day), hour, int(minute))
    except:
        return pd.NaT

# 載入新聞資料
df = pd.read_csv('app_news_multiangle/dataset/yahoo_news_with_media.csv', sep='|')
df['date'] = df['date'].apply(convert_chinese_date)
df.dropna(subset=['date'], inplace=True)

# 主頁
def home(request):
    return render(request, 'app_news_multiangle/home.html')



def highlight_summary(text, keywords):

    # 過濾開頭為 ▲ 的句子（通常是圖片說明）
    sentences = re.split(r'[。！？\n]', text)
    valid_sentences = [s for s in sentences if not s.strip().startswith("▲")]

    # 依照關鍵字找出符合的句子
    keywords_sorted = sorted(keywords, key=len, reverse=True)
    pattern = '|'.join(map(re.escape, keywords_sorted))
    matched_sentences = [s for s in valid_sentences if re.search(pattern, s)]

    if not matched_sentences:
        return text[:100] + "..."

    # 關鍵詞粗體
    highlighted_sentences = [
        re.sub(f"({pattern})", r"<b>\1</b>", s) for s in matched_sentences
    ]

    # 回傳多句（限制最多5句）
    return "。".join(highlighted_sentences[:5]) + "..."



@csrf_exempt
def api_cluster_news(request):
    keyword = request.POST.get('keyword', '')
    days = int(request.POST.get('days', '7'))

    end_date = df['date'].max()
    start_date = end_date - timedelta(days=days)

    df['combined'] = df['title'].fillna('') + df['content'].fillna('')
    keyword_lower = keyword.lower()
    df['keyword_count'] = df['combined'].str.lower().str.count(keyword_lower)

    df_query = df[
        (df['keyword_count'] >= 3) &   # 關鍵字 -> 標題和內文
        (df['date'] >= start_date) &
        (df['date'] <= end_date)
    ].copy()

    df_query = df_query.drop_duplicates(subset='link')  #移除重複的link
    df_query = df_query.head(80)

    if df_query.shape[0] < 2:
        return JsonResponse({"clusters": []})

    # TF-IDF 分群   
    vectorizer = TfidfVectorizer(stop_words='english', max_df=0.8)
    X = vectorizer.fit_transform(df_query['content'])
    n_clusters = min(15, max(3, df_query.shape[0] // 2))
    clustering = AgglomerativeClustering(n_clusters=n_clusters) #層次式分群法
    labels = clustering.fit_predict(X.toarray())
    df_query['cluster'] = labels

    raw_clusters = []
    for label in sorted(df_query['cluster'].unique()):
        group = df_query[df_query['cluster'] == label]
        group_sorted = group.sort_values(by='date').head(10)
        first_article = group_sorted.iloc[0]
        articles = []
        all_tags = []

        for _, row in group_sorted.iterrows():
            try:
                tags = eval(row['top_key_freq']) if isinstance(row['top_key_freq'], str) else []
                row_tags = [k for k, v in sorted(tags, key=lambda x: -x[1])[:3]] if tags else []
            except:
                row_tags = []
            all_tags.extend(row_tags)

        try:
            tag_counts = Counter(all_tags).most_common(3)
            cluster_title = " / ".join([tag for tag, _ in tag_counts]) if tag_counts else first_article['title']
            tag_list = [tag for tag, _ in tag_counts]
        except:
            tag_counts = []
            tag_list = []
            cluster_title = first_article['title']


        for _, row in group_sorted.iterrows():
            summary = highlight_summary(row['content'], tag_list)
            try:
                tags = eval(row['top_key_freq']) if isinstance(row['top_key_freq'], str) else []
                row_tags = [k for k, v in sorted(tags, key=lambda x: -x[1])[:3]] if tags else []
            except:
                row_tags = []

            articles.append({
                'title': row['title'],
                'source': row['media'] if 'media' in row and pd.notna(row['media']) else '未知媒體',
                'date': row['date'].strftime('%Y-%m-%d'),
                'summary': summary,
                'tags': row_tags,
                'link': row['link']
            })

        raw_clusters.append({
            'title': cluster_title,
            'articles': articles,
            'tags': set(tag_list)
        })


    # 合併主題相似群組（Jaccard 相似度 > 0.7）
    """ 群組1:川普 / 美國 / 關稅

        群組2:關稅 / 美國 / 川普

        群組3:美國 / 關稅 / 產品   """

    merged_clusters = []
    used = set()

    for i, ci in enumerate(raw_clusters):
        if i in used:
            continue
        merged = ci.copy()
        merged_indices = {i}

        for j, cj in enumerate(raw_clusters):
            if j <= i or j in used:
                continue
            # Jaccard similarity
            if len(ci['tags'] | cj['tags']) == 0:
                continue
            sim = len(ci['tags'] & cj['tags']) / len(ci['tags'] | cj['tags'])  # 交集/聯集
            if sim >= 0.7:
                merged['articles'].extend(cj['articles'])
                merged['tags'] |= cj['tags']
                merged_indices.add(j)

        merged['title'] = " / ".join(list(merged['tags'])[:3])
        merged_clusters.append(merged)
        used |= merged_indices

    # 最後最多保留 10 個主題
    final_clusters = sorted(merged_clusters, key=lambda c: len(c['articles']), reverse=True)[:10]

    # 補上開始與結束日期
    result = []
    for c in final_clusters:
        articles_sorted = sorted(c['articles'], key=lambda x: x['date'])
        result.append({
            'cluster_title': c['title'],
            'start_date': articles_sorted[0]['date'],
            'end_date': articles_sorted[-1]['date'],
            'first_source': articles_sorted[0]['source'],
            'articles': articles_sorted[:10]
        })

    return JsonResponse({"clusters": result})