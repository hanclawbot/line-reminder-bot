"""
LINE 每日提醒機器人
"""

import os
from flask import Flask, request, Response
from linebot import LineBotApi, WebhookHandler
from linebot.models import MessageEvent, TextMessage, TextSendMessage

app = Flask(__name__)

# 環境變數 - 使用 os.getenv
LINE_CHANNEL_ACCESS_TOKEN = os.getenv('LINE_CHANNEL_ACCESS_TOKEN', '')
LINE_CHANNEL_SECRET = os.getenv('LINE_CHANNEL_SECRET', '')

print(f"TOKEN: {'OK' if LINE_CHANNEL_ACCESS_TOKEN else 'MISSING'}")
print(f"SECRET: {'OK' if LINE_CHANNEL_SECRET else 'MISSING'}")

# 建立 Flask 應用
@app.route('/')
def home():
    return 'LINE Bot is running!'

@app.route('/callback', methods=['POST'])
def callback():
    try:
        handler.handle(request.get_data(as_text=True), request.headers.get('X-Line-Signature', ''))
    except Exception as e:
        print(f"Error: {e}")
    return 'OK'

# 建立 handler (Lazy initialization)
def get_handler():
    if not hasattr(get_handler, '_instance'):
        if LINE_CHANNEL_ACCESS_TOKEN and LINE_CHANNEL_SECRET:
            get_handler._instance = WebhookHandler(LINE_CHANNEL_SECRET)
        else:
            get_handler._instance = None
    return get_handler._instance

handler = get_handler()

# 註冊訊息處理
if handler:
    @handler.add(MessageEvent, message=TextMessage)
    def handle_message(event):
        user_id = event.source.user_id
        text = event.message.text.strip()
        line_bot_api = LineBotApi(LINE_CHANNEL_ACCESS_TOKEN)
        
        if text in ["help", "幫助", "?"]:
            line_bot_api.reply_message(event.reply_token, TextSendMessage(text="""📋 每日提醒機器人

• 設定提醒 [時間] [內容]
• 列出提醒
• 清除所有
• 幫助"""))
            return
        
        if text in ["列出提醒", "list"]:
            line_bot_api.reply_message(event.reply_token, TextSendMessage(text="目前沒有提醒"))
            return
        
        if text in ["清除所有", "clear"]:
            line_bot_api.reply_message(event.reply_token, TextSendMessage(text="已清除"))
            return
        
        if text.startswith("設定提醒"):
            line_bot_api.reply_message(event.reply_token, TextSendMessage(text="✅ 提醒已設定"))
            return
        
        line_bot_api.reply_message(event.reply_token, TextSendMessage(text="請輸入「幫助」"))

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
