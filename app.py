
import os
import tempfile
from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.models import MessageEvent, ImageMessage, TextSendMessage, ImageSendMessage
from linebot.exceptions import InvalidSignatureError
from google.cloud import vision
from google.oauth2 import service_account

app = Flask(__name__)

# LINE credentials from environment variables
line_bot_api = LineBotApi(os.getenv("LINE_CHANNEL_ACCESS_TOKEN"))
handler = WebhookHandler(os.getenv("LINE_CHANNEL_SECRET"))

# Google Vision credentials from local JSON
vision_client = vision.ImageAnnotatorClient(
    credentials=service_account.Credentials.from_service_account_file("linebot-462603-4cdf0a883415.json")
)

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
        temp_path = tf.name

    with open(temp_path, "rb") as img_file:
        content = img_file.read()
    image = vision.Image(content=content)
    response = vision_client.label_detection(image=image)
    labels = [label.description.lower() for label in response.label_annotations]

    # 分類條件
    if any(k in labels for k in ["foam", "polystyrene"]):
        label = "保麗龍"
        image_url = "https://raw.githubusercontent.com/sinkai2025/ctebot/main/保麗龍.jpg"
    elif any(k in labels for k in ["bottle", "plastic"]):
        label = "寶特瓶"
        image_url = "https://raw.githubusercontent.com/sinkai2025/ctebot/main/保麗龍.jpg"
    elif any(k in labels for k in ["cardboard", "carton"]):
        label = "紙箱"
        image_url = "https://raw.githubusercontent.com/sinkai2025/ctebot/main/紙類.jpg"
    else:
        label = "無法判別"
        image_url = "https://raw.githubusercontent.com/sinkai2025/ctebot/main/default.jpg"

    suggestion = f"這是 {label}，請依規定分類處理。"
    messages = [
        TextSendMessage(text=suggestion),
        ImageSendMessage(original_content_url=image_url, preview_image_url=image_url)
    ]
    line_bot_api.reply_message(event.reply_token, messages)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
