from django.shortcuts import render
import pandas as pd
import ast
import json

def load_data_scchen():
    df = pd.read_csv('app_voice_of/dataset/Trump_data.csv')
    response = df.set_index('name')['value'].to_dict()

    # 資料轉為正確型別
    response['freqByDate'] = json.dumps(ast.literal_eval(response['freqByDate']))
    response['freqByCate'] = json.dumps(ast.literal_eval(response['freqByCate']))
    response['category'] = json.dumps(ast.literal_eval(response['category']))

    # 額外加入展示用資料
    response['person_name'] = '唐納．川普'
    response['description'] = '觀察近期新聞中川普的出現情形，統計其總曝光次數與分類分布。'
    response['img_url'] = '/static/img/trump.jpg'

    global response_data
    response_data = response

load_data_scchen()

def home(request):
    return render(request, 'app_voice_of/home.html', response_data)

print('app_voice_of was loaded!')
