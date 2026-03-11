"""
LINE 每日提醒機器人 - 簡化版
"""

import os
import json
from flask import Flask, request, jsonify
import hashlib
import hmac
import base64

app = Flask(__name__)

# 環境變數
LINE_CHANNEL_ACCESS_TOKEN = os.getenv('LINE_CHANNEL_ACCESS_TOKEN', '')
LINE_CHANNEL_SECRET = os.getenv('LINE_CHANNEL_SECRET', '')

print(f"TOKEN: {'OK' if LINE_CHANNEL_ACCESS_TOKEN else 'MISSING'}")
print(f"SECRET: {'OK' if LINE_CHANNEL_SECRET else 'MISSING'}")

# 儲存提醒
reminders = {}

def verify_signature(body, signature):
    """驗證 LINE Webhook 簽名"""
    key = LINE_CHANNEL_SECRET.encode()
    hash = hmac.new(key, body.encode(), hashlib.sha256).digest()
    return base64.b64encode(hash).decode() == signature

@app.route('/')
def home():
    return 'LINE Bot is running!'

@app.route('/callback', methods=['POST'])
def callback():
    signature = request.headers.get('X-Line-Signature', '')
    body = request.get_data(as_text=True)
    
    # 驗證簽名
    if LINE_CHANNEL_SECRET and not verify_signature(body, signature):
        print("簽名驗證失敗")
        return 'OK', 400
    
    try:
        data = json.loads(body)
        events = data.get('events', [])
        
        for event in events:
            if event.get('type') == 'message' and event.get('message', {}).get('type') == 'text':
                handle_text_message(event)
        
    except Exception as e:
        print(f"Error: {e}")
    
    return 'OK'

def handle_text_message(event):
    """處理文字訊息"""
    reply_token = event.get('replyToken')
    user_id = event.get('source', {}).get('userId')
    text = event.get('message', {}).get('text', '').strip()
    
    reply_text = ""
    
    if text in ["help", "幫助", "?"]:
        reply_text = """📋 每日提醒機器人

• 設定提醒 [時間] [內容]
• 列出提醒
• 清除所有
• 幫助"""
    
    elif text in ["列出提醒", "list"]:
        if user_id in reminders and reminders[user_id]:
            reply_text = "📝 你的提醒：\n"
            for i, r in enumerate(reminders[user_id], 1):
                reply_text += f"{i}. {r['time']} - {r['content']}\n"
        else:
            reply_text = "目前沒有提醒"
    
    elif text in ["清除所有", "clear"]:
        reminders[user_id] = []
        reply_text = "✅ 已清除"
    
    elif text.startswith("設定提醒"):
        import re
        content = text[4:].strip()
        match = re.search(r'(\d{1,2}:\d{2})', content)
        if match:
            time = match.group(1)
            reminder_content = content.replace(time, "").strip()
            if user_id not in reminders:
                reminders[user_id] = []
            reminders[user_id].append({"time": time, "content": reminder_content})
            reply_text = f"✅ 已設定：{time} {reminder_content}"
        else:
            reply_text = "請指定時間，如：設定提醒 09:00 喝水"
    
    else:
        reply_text = "請輸入「幫助」"
    
    if reply_text:
        send_reply(reply_token, reply_text)

def send_reply(reply_token, text):
    """發送回覆訊息"""
    import requests
    
    url = 'https://api.line.me/v2/bot/message/reply'
    headers = {
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {LINE_CHANNEL_ACCESS_TOKEN}'
    }
    data = {
        'replyToken': reply_token,
        'messages': [{'type': 'text', 'text': text}]
    }
    
    try:
        r = requests.post(url, headers=headers, json=data)
        print(f"回覆結果: {r.status_code}")
    except Exception as e:
        print(f"回覆錯誤: {e}")

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
