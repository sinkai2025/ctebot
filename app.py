
import os
import tempfile
from flask import Flask, request, abort
from dotenv import load_dotenv
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, ImageMessage, TextSendMessage, ImageSendMessage

from google.cloud import vision
import io
import json

# 初始化
load_dotenv()
app = Flask(__name__)
line_bot_api = LineBotApi(os.getenv("LINE_CHANNEL_ACCESS_TOKEN"))
handler = WebhookHandler(os.getenv("LINE_CHANNEL_SECRET"))

# Google Vision 用的金鑰
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "linebot-462603-c25066979a2a.json"
vision_client = vision.ImageAnnotatorClient()

@app.route("/callback", methods=['POST'])
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
    # 儲存圖片
    message_content = line_bot_api.get_message_content(event.message.id)
    with tempfile.NamedTemporaryFile(delete=False, suffix=".jpg") as tf:
        tf.write(message_content.content)
        temp_path = tf.name

    # 使用 Google Vision 辨識圖片
    with io.open(temp_path, 'rb') as image_file:
        content = image_file.read()
    image = vision.Image(content=content)
    response = vision_client.label_detection(image=image)
    labels = [label.description.lower() for label in response.label_annotations]

    # 判斷類型與建議
    if any(keyword in labels for keyword in ['styrofoam', 'foam']):
        label = "保麗龍"
        suggestion = "請丟入標有保麗龍的美固籠。"
        image_url = "https://raw.githubusercontent.com/sinkai2025/ctebot/main/保麗龍.jpg"
    elif any(keyword in labels for keyword in ['cardboard', 'box']):
        label = "紙箱"
        suggestion = "請折疊後放入紙類資源回收桶。"
        image_url = "https://raw.githubusercontent.com/sinkai2025/ctebot/main/紙箱.jpg"
    elif any(keyword in labels for keyword in ['bottle', 'plastic']):
        label = "寶特瓶"
        suggestion = "請清洗後放入塑膠類回收桶。"
        image_url = "https://raw.githubusercontent.com/sinkai2025/ctebot/main/寶特瓶.jpg"
    else:
        label = "無法辨識"
        suggestion = "請重新拍攝或提供其他角度。"
        image_url = "https://raw.githubusercontent.com/sinkai2025/ctebot/main/未知.jpg"

    # 回覆用戶
    line_bot_api.reply_message(
        event.reply_token,
        [
            TextSendMessage(text=f"{label}\n{suggestion}"),
            ImageSendMessage(original_content_url=image_url, preview_image_url=image_url)
        ]
    )

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=10000)
