import os
import tempfile
from flask import Flask, request, abort
from dotenv import load_dotenv
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, ImageMessage, TextSendMessage

# 載入 .env 設定
load_dotenv()
app = Flask(__name__)

# 設定 LINE 憑證
line_bot_api = LineBotApi(os.getenv("LINE_CHANNEL_ACCESS_TOKEN"))
handler = WebhookHandler(os.getenv("LINE_CHANNEL_SECRET"))

# webhook 路由
@app.route("/callback", methods=['POST'])
def callback():
    signature = request.headers.get("X-Line-Signature", "")
    body = request.get_data(as_text=True)
    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)
    return 'OK'

# 圖片訊息處理邏輯
@handler.add(MessageEvent, message=ImageMessage)
def handle_image(event):
    message_content = line_bot_api.get_message_content(event.message.id)
    with tempfile.NamedTemporaryFile(delete=False, suffix=".jpg") as tf:
        tf.write(message_content.content)
        image_path = tf.name

    # 模擬分類辨識
    label = "保麗龍"
    suggestion = "這是保麗龍，請丟入塑膠類回收桶。"

    line_bot_api.reply_message(
        event.reply_token,
    [
        TextSendMessage(text="這是測試訊息"),
        ImageSendMessage(
            original_content_url="https://i.imgur.com/xyz1234.jpg",  # ← 換成你能開啟的圖片網址
            preview_image_url="https://i.imgur.com/xyz1234.jpg"
        )
    ]
    )

# 指定 host/port，適用於 Render
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
