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

############# Crawl the data #############


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


@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(text=event.message.text))


if __name__ == "__main__":
    app.run()
