import os
import tempfile
from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, ImageMessage, TextSendMessage, ImageSendMessage
from google.cloud import vision

app = Flask(__name__)

# 初始化 LINE BOT
line_bot_api = LineBotApi(os.getenv("LINE_CHANNEL_ACCESS_TOKEN"))
handler = WebhookHandler(os.getenv("LINE_CHANNEL_SECRET"))

# 設定 Google Vision 憑證環境變數
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "linebot-462603-4cdf0a883415.json"

@app.route("/callback", methods=['POST'])
def callback():
    signature = request.headers.get("X-Line-Signature", "")
    body = request.get_data(as_text=True)
    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)
    return 'OK'

@handler.add(MessageEvent, message=ImageMessage)
def handle_image(event):
    message_content = line_bot_api.get_message_content(event.message.id)
    with tempfile.NamedTemporaryFile(delete=False, suffix=".jpg") as tf:
        tf.write(message_content.content)
        image_path = tf.name

    # 呼叫 Google Vision 辨識
    client = vision.ImageAnnotatorClient()
    with open(image_path, "rb") as image_file:
        content = image_file.read()
    image = vision.Image(content=content)
    response = client.label_detection(image=image)
    labels = [label.description for label in response.label_annotations]
    label = labels[0] if labels else "未知物品"

    # 提示語 & 測試圖片網址（你可替換）
    suggestion = f"這是 {label}，請依規定分類處理。"
    image_url = "https://raw.githubusercontent.com/sinkai2025/ctebot/main/保麗龍.jpg"

    messages = [
        TextSendMessage(text=f"{label}
{suggestion}"),
        ImageSendMessage(
            original_content_url=image_url,
            preview_image_url=image_url
        )
    ]
    line_bot_api.reply_message(event.reply_token, messages)

if __name__ == "__main__":
    app.run()
