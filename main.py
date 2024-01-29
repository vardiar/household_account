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

app = Flask(__name__)

## handler = WebhookHandler('e0d9b8bd9c4f359fc11abb50c5d9c401')
handler = WebhookHandler(os.environ.get("CHANNEL_SECRET"))
configuration = Configuration(access_token=os.environ.get("CHANNEL_ACCESS_TOKEN"))


@app.route("/callback", methods=['POST'])
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
      msg_dict = {
          "日付: ": f"{msg_list[0]}",
          "区分: ": "支出",
          "項目: ": f"{msg_list[1]}",
          "金額: ": f"{msg_list[2]}",
      }
      dmsg = "この内容で記録するよ！\n"
      message = '\n'.join([f"{key}{value}" for key, value in msg_dict.items()])
      line_bot_api.reply_message_with_http_info(
        ReplyMessageRequest(
          reply_token=event.reply_token,
          messages=[TextMessage(text=dmsg+message)]
        )
      )

if __name__ == "__main__":
    port = int(os.getenv("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)

