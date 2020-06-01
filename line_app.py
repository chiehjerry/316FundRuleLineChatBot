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
