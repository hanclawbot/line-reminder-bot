"""
LINE 每日提醒機器人
"""

import os
from flask import Flask, request, Response
from linebot import LineBotApi, WebhookHandler
from linebot.models import MessageEvent, TextMessage, TextSendMessage

app = Flask(__name__)

# 環境變數
LINE_CHANNEL_ACCESS_TOKEN = os.environ.get('LINE_CHANNEL_ACCESS_TOKEN', '')
LINE_CHANNEL_SECRET = os.environ.get('LINE_CHANNEL_SECRET', '')

print(f"TOKEN: {'OK' if LINE_CHANNEL_ACCESS_TOKEN else 'MISSING'}")
print(f"SECRET: {'OK' if LINE_CHANNEL_SECRET else 'MISSING'}")

# 初始化 API 和 Handler
if LINE_CHANNEL_ACCESS_TOKEN and LINE_CHANNEL_SECRET:
    line_bot_api = LineBotApi(LINE_CHANNEL_ACCESS_TOKEN)
    handler = WebhookHandler(LINE_CHANNEL_SECRET)
else:
    line_bot_api = None
    handler = None
    print("錯誤：環境變數未設定")

# 儲存提醒
reminders = {}

@app.route('/')
def home():
    return 'LINE Bot is running!'

@app.route('/callback', methods=['POST'])
def callback():
    if not handler:
        print("Error: Handler not initialized")
        return 'OK', 500
    
    signature = request.headers.get('X-Line-Signature', '')
    body = request.get_data(as_text=True)
    
    try:
        handler.handle(body, signature)
    except Exception as e:
        print(f"Callback error: {e}")
    
    return 'OK'

# 只有在 handler 初始化成功時才註冊事件處理
if handler:
    @handler.add(MessageEvent, message=TextMessage)
    def handle_message(event):
        user_id = event.source.user_id
        text = event.message.text.strip()
        
        # 幫助
        if text in ["help", "幫助", "?"]:
            help_text = """📋 LINE 每日提醒機器人

    可用指令：
    • 設定提醒 [時間] [內容]
    • 列出提醒
    • 刪除提醒 [編號]
    • 清除所有
    • 幫助"""
            line_bot_api.reply_message(event.reply_token, TextSendMessage(text=help_text))
            return
        
        # 列出提醒
        if text in ["列出提醒", "list", "我的提醒"]:
            if user_id not in reminders or not reminders[user_id]:
                line_bot_api.reply_message(event.reply_token, TextSendMessage(text="目前沒有設定任何提醒"))
                return
            
            response = "📝 你的提醒列表：\n\n"
            for i, rem in enumerate(reminders[user_id], 1):
                response += f"{i}. ⏰ {rem['time']} - {rem['content']}\n"
            line_bot_api.reply_message(event.reply_token, TextSendMessage(text=response))
            return
        
        # 清除所有
        if text in ["清除所有", "clear"]:
            if user_id in reminders:
                reminders[user_id] = []
            line_bot_api.reply_message(event.reply_token, TextSendMessage(text="✅ 已清除所有提醒"))
            return
        
        # 設定提醒
        if text.startswith("設定提醒"):
            import re
            content = text[4:].strip()
            time_match = re.search(r'(\d{1,2}:\d{2})', content)
            
            if not time_match:
                line_bot_api.reply_message(event.reply_token, TextSendMessage(text="❌ 請指定時間，格式：設定提醒 09:00 喝水"))
                return
            
            time_str = time_match.group(1)
            reminder_content = content.replace(time_str, "").strip()
            
            if not reminder_content:
                line_bot_api.reply_message(event.reply_token, TextSendMessage(text="❌ 請指定提醒內容"))
                return
            
            if user_id not in reminders:
                reminders[user_id] = []
            
            reminders[user_id].append({"time": time_str, "content": reminder_content})
            line_bot_api.reply_message(event.reply_token, TextSendMessage(text=f"✅ 已設定提醒：⏰ {time_str} - {reminder_content}"))
            return
        
        # 預設
        line_bot_api.reply_message(event.reply_token, TextSendMessage(text="請輸入「幫助」查看指令"))

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
