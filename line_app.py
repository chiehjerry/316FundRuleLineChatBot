############# Load the packages #############

### Crawl packages ###
import requests
import pandas as pd
from bs4 import BeautifulSoup
### Crawl packages ###

### Line chatbot packages ###
# Load the flask
from flask import Flask, request, abort

from linebot import (
    LineBotApi, WebhookHandler
)
# Load linebot to do InvalidSignatureError
from linebot.exceptions import (
    InvalidSignatureError
)
# Load linebot message component
from linebot.models import (
    MessageEvent, TextMessage, TextSendMessage,
)
### Line chatbot packages ###
############# Load the packages #############

############# Set about the environment #############

app = Flask(__name__)

headers = {
    "User-Agent": "Mozilla/5.0 (Linux; Android 6.0; Nexus 5 Build/MRA58N) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/83.0.4103.61 Mobile Safari/537.36"
}

line_bot_api = LineBotApi('YOUR_CHANNEL_ACCESS_TOKEN')
handler = WebhookHandler('YOUR_CHANNEL_SECRET')

############# Set about the environment #############

############# Crawl the data #############

# Store the fund
fund_map_dict = {}

# Init the fund list (The case use 'dict',or use 'google sheet' too.)


def init_fund_list():
    # Sent the request to get the URL
    resp = requests.get(
        'https://www.sitca.org.tw/ROC/Industry/IN2421.aspx?txtMonth=02&txtYear=2020', headers=headers)
    # BeautifulSoup the object
    soup = BeautifulSoup(resp.text, 'html.parser')
    # Select the fund list
    table_content = soup.select('#ctl00_ContentPlaceHolder1_TableClassList')[0]
    # Select the fund list about 'a'
    fund_links = table_content.select('a')

    # Get the fund_links text
    for fund_link in fund_links:
        if fund_link.text:
            fund_name = fund_link.text
            fund_group_id = fund_link['href'].split('txtGROUPID=')[1]
            fund_map_dict[fund_name] = fund_group_id


def fetch_fund_rule_items(year, month, group_id):
    fetch_url = f'https://www.sitca.org.tw/ROC/Industry/IN2422.aspx?txtYEAR={year}&txtMONTH={month}&txtGROUPID={group_id}'
    print(year, month, group_id)

    resp = requests.get(fetch_url, headers=headers)
    # BeautifulSoup the object
    soup = BeautifulSoup(resp.text, 'html.parser')

    # Craw the web data
    resp = requests.get(
        'https://www.sitca.org.tw/ROC/Industry/IN2422.aspx?txtYEAR=2020&txtMONTH=04&txtGROUPID=EUCA000507', headers=headers)

    soup = BeautifulSoup(resp.text, 'html.parser')

    # Find that craw the Morningstar table by id ctl00_ContentPlaceHolder1_TableClassList , then craw the first
    table_content = soup.select('#ctl00_ContentPlaceHolder1_TableClassList')[0]

    # Use BeautifulSoup to prettify the parsed-object, and then table be loaded by pandas,then craw the first
    # the encoding code is  UTF-8
    fund_df = pd.read_html(table_content.prettify(), encoding='utf-8')[1]

    # Data pre-processing to drop the needless row.
    fund_df = fund_df.drop(index=[0])
    # Set the row one to Header
    fund_df.columns = fund_df.iloc[0]
    # Drop the needless row.
    fund_df = fund_df.drop(index=[1])
    # Reset_index
    fund_df.reset_index(drop=True, inplace=True)
    # NaN -> 0
    fund_df = fund_df.fillna(value=0)
    # Transform the data from object to float
    fund_df['一個月'] = fund_df['一個月'].astype(float)
    fund_df['三個月'] = fund_df['三個月'].astype(float)
    fund_df['六個月'] = fund_df['六個月'].astype(float)
    fund_df['一年'] = fund_df['一年'].astype(float)
    fund_df['二年'] = fund_df['二年'].astype(float)
    fund_df['三年'] = fund_df['三年'].astype(float)
    fund_df['五年'] = fund_df['五年'].astype(float)
    fund_df['自今年以來'] = fund_df['自今年以來'].astype(float)

    # The number of top one-half
    half_of_row_count = len(fund_df.index) // 2  # // is catching the integer

    # The 316 rule ，ascending True is small to large，nlargest to catch the data top one-half.
    rule_3_df = fund_df.sort_values(
        by=['三年'], ascending=['True']).nlargest(half_of_row_count, '三年')

    rule_1_df = fund_df.sort_values(
        by=['一年'], ascending=['True']).nlargest(half_of_row_count, '一年')
    rule_6_df = fund_df.sort_values(
        by=['六個月'], ascending=['True']).nlargest(half_of_row_count, '六個月')

    # Get the 'inner' by two and two , using merge.
    rule_31_df = pd.merge(rule_3_df, rule_1_df, how='inner')
    rule_316_df = pd.merge(rule_31_df, rule_6_df, how='inner')
    print('====316 法則====\n', rule_316_df)

    fund_rule_items_str = ''

    if not rule_6_df.empty:
        for _, row in rule_316_df.iterrows():
            fund_rule_items_str += f'{row["基金名稱"]},{row["三年"]}, {row["一年"]},{row["六個月"]}\n'
    return fund_rule_items_str

############# Crawl the data #############

############# Line chatbot #############


@app.route("/callback", methods=['POST'])
def callback():
    # get X-Line-Signature header value
    signature = request.headers['X-Line-Signature']

    # get request body as text
    body = request.get_data(as_text=True)
    # handle webhook body
    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        print("Invalid signature. Please check your channel access token/channel secret.")
        abort(400)

    return 'OK'


# decorator to check the event is  MessageEvent instance ，event.message is TextMessage instance 。so process the handler of TextMessage
@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    # To decide Component to  Channel by TextSendMessage
    user_input = event.message.text
    if user_input == '@基金列表':
        fund_list_str = ''
        for fund_name in fund_map_dict:
            fund_list_str += fund_name + '\n'
        line_bot_api.reply_message(
            event.reply_token, TextSendMessage(text=fund_list_str))
    elif user_input in fund_map_dict:
        group_id = fund_map_dict[user_input]
        print('開始篩選！')
        fund_rule_items_str = fetch_fund_rule_items('2020', '04', group_id)
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text=fund_rule_items_str))
    else:
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text='請輸入正確指令'))


############# Line chatbot #############

############# Run the app #############

if __name__ == "__main__":
  # Run Flask server
    init_fund_list()
    app.run()

############# Run the app #############
