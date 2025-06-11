import os
import tempfile
from flask import Flask, request, abort
from dotenv import load_dotenv
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, ImageMessage, TextSendMessage, ImageSendMessage

load_dotenv()
app = Flask(__name__)
line_bot_api = LineBotApi(os.getenv("LINE_CHANNEL_ACCESS_TOKEN"))
handler = WebhookHandler(os.getenv("LINE_CHANNEL_SECRET"))

@app.route("/callback", methods=["POST"])
def callback():
    signature = request.headers.get("X-Line-Signature", "")
    body = request.get_data(as_text=True)
    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)
    return "OK"

@handler.add(MessageEvent, message=ImageMessage)
def handle_image(event):
    message_content = line_bot_api.get_message_content(event.message.id)
    with tempfile.NamedTemporaryFile(delete=False, suffix=".jpg") as tf:
        tf.write(message_content.content)
        image_path = tf.name

    # 模擬分類辨識
    label = "保麗龍"
    suggestion = f"這是「{label}」，請依規定分類處理。"
    image_url = "https://raw.githubusercontent.com/sinkai2025/ctebot/main/%E4%BF%9D%E9%BA%97%E9%BE%8D.jpg"

    messages = [
        TextSendMessage(text=f"{label}\n{suggestion}"),
        ImageSendMessage(
            original_content_url=image_url,
            preview_image_url=image_url
        )
    ]
    line_bot_api.reply_message(event.reply_token, messages)

if __name__ == "__main__":
   app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
