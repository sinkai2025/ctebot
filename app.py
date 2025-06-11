
import os
import tempfile
from flask import Flask, request, abort
from dotenv import load_dotenv
from linebot import LineBotApi, WebhookHandler
from linebot.models import MessageEvent, ImageMessage, TextSendMessage, ImageSendMessage
from linebot.exceptions import InvalidSignatureError
from google.cloud import vision

# === 設定金鑰（Render 的 Secret Files 對應這個路徑） ===
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "/etc/secrets/linebot-credentials.json"

# === 初始化 ===
load_dotenv()
app = Flask(__name__)
line_bot_api = LineBotApi(os.getenv("LINE_CHANNEL_ACCESS_TOKEN"))
handler = WebhookHandler(os.getenv("LINE_CHANNEL_SECRET"))

# === 初始化 Google Vision 客戶端 ===
vision_client = vision.ImageAnnotatorClient()

# === LINE Webhook ===
@app.route("/callback", methods=["POST"])
def callback():
    signature = request.headers.get("X-Line-Signature", "")
    body = request.get_data(as_text=True)
    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)
    return "OK"

# === 處理圖片訊息 ===
@handler.add(MessageEvent, message=ImageMessage)
def handle_image(event):
    # 下載使用者傳來的圖片
    message_content = line_bot_api.get_message_content(event.message.id)
    with tempfile.NamedTemporaryFile(delete=False, suffix=".jpg") as tf:
        tf.write(message_content.content)
        temp_image_path = tf.name

    # 使用 Google Vision API 分析圖片
    with open(temp_image_path, "rb") as image_file:
        content = image_file.read()
        image = vision.Image(content=content)
        response = vision_client.label_detection(image=image)
        labels = response.label_annotations

    if not labels:
        label_desc = "無法辨識圖片內容"
    else:
        label_desc = f"辨識結果：{labels[0].description}"

    # 準備回覆訊息
    messages = [
        TextSendMessage(text=label_desc),
        ImageSendMessage(
            original_content_url="https://raw.githubusercontent.com/sinkai2025/ctebot/main/保麗龍.jpg",
            preview_image_url="https://raw.githubusercontent.com/sinkai2025/ctebot/main/保麗龍.jpg"
        )
    ]
    line_bot_api.reply_message(event.reply_token, messages)

# === 啟動伺服器 ===
if __name__ == "__main__":
    app.run(host='0.0.0.0', port=10000)
