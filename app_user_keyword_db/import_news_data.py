import os
import sys
import pandas as pd
import argparse
from datetime import datetime
import pathlib
import django

# 新增：加入專案根目錄
project_root = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(project_root)
sys.path.insert(0, project_root)

# 設定 Django 環境
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'website_configs.settings')
os.environ["DJANGO_ALLOW_ASYNC_UNSAFE"] = "true"
django.setup()

from app_user_keyword_db.models import NewsData




# Read CSV file
csv_file_path = './app_user_keyword/dataset/yahoo_news_preprocessed.csv'
df = pd.read_csv(csv_file_path, sep='|')


if 'item_id' not in df.columns:
    df.insert(0, 'item_id', range(100001, 100001 + len(df)))


def parse_date(date_str):
    try:
        # 嘗試 ISO 格式
        return datetime.strptime(date_str, '%Y-%m-%d').date()
    except ValueError:
        try:
            # 替換中文「上午」「下午」
            date_str = date_str.replace('上午', 'AM').replace('下午', 'PM')
            # 嘗試解析格式：2025年4月13日 PM3:19
            dt = datetime.strptime(date_str, '%Y年%m月%d日 %p%I:%M')
            return dt.date()
        except Exception:
            raise ValueError(f"Unrecognized date format: {date_str}")


# Process each row and create a NewsData object
for idx, row in df.iterrows():
    try:
        # Convert date string to datetime object
        date_obj = parse_date(row['date'])     

        # Create or update NewsData object
        news_data, created = NewsData.objects.update_or_create(
            item_id=row['item_id'],
            defaults={
                'date': date_obj,
                'category': row['category'],
                'title': row['title'],
                'content': row['content'],
                #'sentiment': row['sentiment'],
                #'summary': row['summary'],
                'top_key_freq': row['top_key_freq'],
                'tokens': row['tokens'],
                'tokens_v2': row['tokens_v2'],
                'entities': row['entities'],
                'token_pos': row['token_pos'],
                'link': row['link'],
                'photo_link': row['photo_link'] if row['photo_link'] != "" and not pd.isna(row['photo_link']) else None,
            }
        )
        if created:
            print(f"Created new NewsData object with item_id: {row['item_id']}")
        else:
            print(f"Updated existing NewsData object with item_id: {row['item_id']}")
    except Exception as e:
        print(f"Error at row {idx}: {e}")
        print(row)