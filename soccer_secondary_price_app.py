
# -*- coding: utf-8 -*-
import pandas as pd
import numpy as np
import seaborn as sns
import requests
from bs4 import BeautifulSoup
import re
import japanize_matplotlib
import matplotlib.pyplot as plt
from datetime import datetime, timedelta
import time
import streamlit as st

# 枚数を変換するコード
def extract_numbers(text):
    match = re.search(r'\d+', text)
    return int(match.group()) if match else None

# スクレイピングのmain
def scrape(team):
    base_url = f'https://ticketjam.jp/tickets/{team}'

    data_get_date = datetime.today().strftime('%Y%m%d')

    # 空のデータを作成
    events = []
    event_dates = []
    details = []
    prices = []
    amounts = []
    status_box = []

    # 404エラーを防ぐためheadersを追加
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }

    page_num = 1  # 初期化の修正

    while True:
        if page_num == 1:
            page_url = f'{base_url}'
        else:
            page_url = f'{base_url}?page={page_num}'

        response = requests.get(page_url, headers=headers)
        soup = BeautifulSoup(response.content, 'html.parser')
        eventlist_items = soup.find_all(class_=['eventlist__item active', 'eventlist__item bg-gray'])

        # eventlist__items内の要素ごとにループ処理
        for item in eventlist_items:
            # Event name
            event = item.find('div', class_='eventlist__title')
            if event:
                # Remove the small tags
                for small in event.find_all('small'):
                    small.decompose()
                event_text = event.get_text(separator=' ', strip=True)
                events.append(event_text)
            else:
                events.append(None)

            # Event date
            event_date = item.find('div', class_='venue')
            if event_date:
                event_date_text = event_date.get_text(strip=True)
                date_match = re.search(r'\d{4}/\d{2}/\d{2}', event_date_text)
                if date_match:
                    date_str = date_match.group()
                    formatted_date = datetime.strptime(date_str, '%Y/%m/%d').strftime('%Y%m%d')
                    event_dates.append(formatted_date)
                else:
                    event_dates.append(None)
            else:
                event_dates.append(None)

            # Event detail
            detail = item.find('div', class_='eventlist__description')
            if detail:
                detail_text = detail.get_text(separator=' ', strip=True)
                details.append(detail_text)
            else:
                details.append(None)

            # Event price
            price = item.find('span', class_='u-text-vivid-red u-text-size-md font-weight-bold')
            if price:
                price_text = price.get_text(strip=True)
                prices.append(price_text)
            else:
                prices.append(None)

            # Event amount
            amount = item.find('span', class_=['ml-1 bold sell-true', 'ml-1 bold'])
            if amount:
                amount_text = amount.get_text(strip=True)
                amounts.append(amount_text)
            else:
                amounts.append(None)

            # Event status
            status_section = item.find('div', class_='eventlist__links')
            if status_section:
                status = status_section.find('span', class_='u-text-vivid-red')
                if status:
                    status_text = status.get_text(strip=True)
                    if status_text in ['取引中', '取引済']:
                        status_box.append(status_text)
                    else:
                        status_box.append('取引前')
                else:
                    status_box.append('取引前')
            else:
                status_box.append('取引前')

        # 次のページがあるか確認しなければ終了
        next_page_element = soup.find('a', rel='next')
        if next_page_element and 'href' in next_page_element.attrs:
            page_num += 1
        else:
            break

        time.sleep(0.1)

    # 取得したデータを用いてデータフレームを作成
    df = pd.DataFrame({
        'data_get_dates': data_get_date,
        'event_dates': event_dates
        'events': events,
        'details': details,
        'prices': prices,
        'amounts': amounts,
        'status': status_box
    })

    # pricesのエラーチェックと変換
    df['prices'] = df['prices'].str.replace(',', '').str.extract(r'(\d+)').astype(float)

    df['amounts'] = df['amounts'].apply(extract_numbers)

    return df

st.title('サッカー 二次流通市場価格 スクレイピング アプリ')

st.markdown("<hr>", unsafe_allow_html=True)

st.markdown("""
### このアプリについて

チケジャムから以下の情報を取得します：

- `data_get_dates`: 今日の日付
- `data_get_dates`: 試合日
- `events`: 試合概要
- `details`: チケットに関する説明
- `prices`: チケット価格
- `amounts`: チケット枚数
- `status`: 取引状況
""")

st.markdown("<hr>", unsafe_allow_html=True)

teams_display = {
    'サッカー日本代表': 'national-team-soccer',
    '明治安田生命J1リーグ': 'meijiyasudaseimei-ji',
    '明治安田生命J2リーグ': 'meijiyasudaseimei-j2',
    'アビスパ福岡': 'avispa',
    'アルビレックス新潟': 'albirex',
    '浦和レッズ': 'reds',
    'ヴィッセル神戸': 'vissel-kobe',
    'FC東京': 'fctokyo',
    'FC町田ゼルビア': 'zelvia',
    'ガンバ大阪': 'gamba-osaka',
    '川崎フロンターレ': 'frontale',
    '鹿島アントラーズ': 'antlers',
    '柏レイソル': 'reysol',
    '京都サンガFC': 'sanga-fc',
    '湘南ベルマーレ': 'bellmare',
    'サガン鳥栖': 'sagan-tosu',
    'サンフレッチェ広島': 'sanfrecce',
    'セレッソ大阪': 'cerezo',
    'ジュビロ磐田': 'jubilo-iwata',
    '東京ヴェルディ': 'verdy',
    '北海道コンサドーレ札幌': 'consadole-sapporo',
    '名古屋グランパス': 'nagoya-grampus',
    '横浜F・マリノス': 'f-marinos'
}

selected_teams_display = st.multiselect('チームを選択してください（五十音順）', teams_display.keys(), default=None)

all_selected = st.checkbox('全てのチームをスクレイピング')

if all_selected:
    selected_teams_display = list(teams_display.keys())

st.markdown("<hr>", unsafe_allow_html=True)

if st.button('スクレイピング開始'):
    all_dfs = []
    with st.spinner('スクレイピング中'):
        for selected_team_display in selected_teams_display:
            team = teams_display[selected_team_display]
            df = scrape(team)  # 引数にteamを追加
            all_dfs.append(df)
        combined_df = pd.concat(all_dfs, ignore_index=True)
        st.write('スクレイピング完了')
        st.dataframe(combined_df)
        csv = combined_df.to_csv(index=False)
        st.download_button(
            label='CSVとしてダウンロード',
            data=csv,
            file_name=f'soccer_secondary_prices_{datetime.today().strftime("%Y%m%d")}.csv',
            mime='text/csv'
        )

        # 箱ひげ図のプロット
        plt.figure(figsize=(10, 6))
        # イベント名の並び順を指定
        sorted_events = combined_df['events'].unique()
        sns.boxplot(data=combined_df, x='events', y='prices', order=sorted_events)
        plt.title('イベントごとの価格 箱ひげ図')
        plt.xticks(rotation=20, fontsize=6)
        plt.savefig("boxplot.png")
        st.pyplot(plt)

        # グラフを保存するボタン
        with open("boxplot.png", "rb") as file:
            btn = st.download_button(
                label="グラフを保存",
                data=file,
                file_name="boxplot.png",
                mime="image/png"
            )

        # 統計情報の計算
        stats_df = combined_df.groupby('events')['prices'].describe().reset_index()

        # 四分位範囲 (IQR) を計算
        stats_df['IQR'] = stats_df['75%'] - stats_df['25%']

        # 平均値を計算
        stats_df['mean'] = combined_df.groupby('events')['prices'].mean().values

        # イベント名の並び順を指定
        stats_df = stats_df.set_index('events').loc[sorted_events].reset_index()

        # 統計情報の表示
        st.write("### 箱ひげ図の詳細情報")
        st.dataframe(stats_df)

        # 統計情報をCSVとしてダウンロードするボタン
        csv_stats = stats_df


        # 統計情報をCSVとしてダウンロードするボタン
        csv_stats = stats_df
