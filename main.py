import os
from flask import Flask, abort, request
from linebot.v3.webhook import (
    WebhookHandler
)
from linebot.v3.exceptions import (
    InvalidSignatureError
)
from linebot.v3.messaging import (
    Configuration,
    ApiClient,
    MessagingApi,
    ReplyMessageRequest,
    TextMessage
)
from linebot.v3.webhooks import (
    MessageEvent,
    TextMessageContent
)
import gspread
import json
from oauth2client.service_account import ServiceAccountCredentials
import string
import re

def connect_gspread(jsonf, key):
  scope = ["https://spreadsheets.google.com/feeds","https://www.googleapis.com/auth/drive"]
  credentials = ServiceAccountCredentials.from_json_keyfile_name(jsonf,scope)
  gc = gspread.authorize(credentials)
  ss_key = key
  worksheet = gc.open_by_key(ss_key).get_worksheet(-1)
  return worksheet

app = Flask(__name__)

handler = WebhookHandler(os.environ.get("CHANNEL_SECRET"))
configuration = Configuration(access_token=os.environ.get("CHANNEL_ACCESS_TOKEN"))

@app.route("/webhook", methods=['POST'])
## @app.route("/callback", methods=['POST'])
def callback():
    signature = request.headers['X-Line-Signature']

    body = request.get_data(as_text=True)
    app.logger.info("Request body: " + body)

    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        app.logger.info("Invalid signature. Please check your channel access token/channel secret.")
        abort(400)

    return 'OK'

@handler.add(MessageEvent, message=TextMessageContent)
def handle_message(event):
    with ApiClient(configuration) as api_client:
      line_bot_api = MessagingApi(api_client)
      msg_list = event.message.text.split(" ")
      msg_list.insert(1,"支出")
      msg_dict = {
          "日付: ": f"{msg_list[0]}",
          "区分: ": f"{msg_list[1]}",
          "項目: ": f"{msg_list[2]}",
          "金額: ": f"{msg_list[3]}",
      }
      dmsg = "この内容で記録するよ！\n"
      message = '\n'.join([f"{key}{value}" for key, value in msg_dict.items()])
      line_bot_api.reply_message_with_http_info(
        ReplyMessageRequest(
          reply_token=event.reply_token,
          messages=[TextMessage(text=dmsg+message)]
        )
      )
      msg_list[-1] = int(re.search(r"\d+",msg_list[-1]).group())
      jsonf = "spread_sheet_secret.json"
      spread_sheet_key = os.environ.get("SPREAD_SHEET_KEY")
      worksheet = connect_gspread(jsonf,spread_sheet_key)
      column_list = list(string.ascii_uppercase)[:len(msg_dict)]
      column_range = worksheet.range(f"{column_list[0]}1:{column_list[0]}{worksheet.row_count}")
      ins_row = next((cell.row for cell in reversed(column_range) if cell.value), None) + 1
      worksheet.append_row(msg_list,table_range=f"{column_list[0]}{ins_row}:{column_list[-1]}{ins_row}")

if __name__ == "__main__":
    port = int(os.getenv("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)
