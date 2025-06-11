import os
import tempfile
from flask import Flask, request, abort
from dotenv import load_dotenv
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, ImageMessage, TextSendMessage, ImageSendMessage
from google.cloud import vision

load_dotenv()
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")

app = Flask(__name__)
line_bot_api = LineBotApi(os.getenv("LINE_CHANNEL_ACCESS_TOKEN"))
handler = WebhookHandler(os.getenv("LINE_CHANNEL_SECRET"))
client = vision.ImageAnnotatorClient()

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

    with open(image_path, 'rb') as image_file:
        content = image_file.read()
    image = vision.Image(content=content)
    response = client.label_detection(image=image)
    labels = [label.description for label in response.label_annotations]

    label = "未知"
    suggestion = "無法辨識，請再嘗試其他角度或光源"
    image_url = None

    for l in labels:
        if "Styrofoam" in l or "Foam" in l:
            label = "保麗龍"
            suggestion = "這是保麗龍，請丟入標有保麗龍之美固籠。"
            image_url = "https://raw.githubusercontent.com/sinkai2025/ctebot/main/保麗龍.jpg"
            break
        elif "Cardboard" in l or "Carton" in l:
            label = "紙箱"
            suggestion = "這是紙箱，請丟入紙類回收。"
            image_url = "https://raw.githubusercontent.com/sinkai2025/ctebot/main/紙箱.jpg"
            break
        elif "Plastic bottle" in l or "Bottle" in l:
            label = "寶特瓶"
            suggestion = "這是寶特瓶，請壓扁後丟入寶特瓶回收桶。"
            image_url = "https://raw.githubusercontent.com/sinkai2025/ctebot/main/寶特瓶.jpg"
            break

    messages = [TextSendMessage(text=f"{label}\n{suggestion}")]
    if image_url:
        messages.append(ImageSendMessage(original_content_url=image_url, preview_image_url=image_url))

    line_bot_api.reply_message(event.reply_token, messages)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
