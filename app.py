import os
import tempfile
from flask import Flask, request, abort
from dotenv import load_dotenv
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, ImageMessage, TextSendMessage, ImageSendMessage

# 載入環境變數
load_dotenv()

app = Flask(__name__)
line_bot_api = LineBotApi(os.getenv("LINE_CHANNEL_ACCESS_TOKEN"))
handler = WebhookHandler(os.getenv("LINE_CHANNEL_SECRET"))

# webhook 接收路由
@app.route("/callback", methods=['POST'])
def callback():
    signature = request.headers.get("X-Line-Signature", "")
    body = request.get_data(as_text=True)
    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)
    return 'OK'

# 圖片訊息處理
@handler.add(MessageEvent, message=ImageMessage)
def handle_image(event):
    message_content = line_bot_api.get_message_content(event.message.id)
    with tempfile.NamedTemporaryFile(delete=False, suffix=".jpg") as tf:
        tf.write(message_content.content)
        image_path = tf.name

    # 模擬分類辨識
    label = "保麗龍"
    suggestion = "這是保麗龍，請丟入標有保麗龍之美固籠。"
    image_url = "https://raw.githubusercontent.com/sinkai2025/ctebot/main/保麗龍.jpg"

    # 回覆圖文訊息
    line_bot_api.reply_message(
        event.reply_token,
        [
            TextSendMessage(text=f"{label}\n{suggestion}"),
            ImageSendMessage(
                original_content_url=image_url,
                preview_image_url=image_url
            )
        ]
    )

# Render 執行
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
