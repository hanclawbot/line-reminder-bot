"""
LINE 每日提醒機器人 - 含定時提醒功能
"""

import os
import json
from flask import Flask, request, jsonify
import hashlib
import hmac
import base64
from datetime import datetime
import threading
import time

app = Flask(__name__)

# 環境變數
LINE_CHANNEL_ACCESS_TOKEN = os.getenv('LINE_CHANNEL_ACCESS_TOKEN', '')
LINE_CHANNEL_SECRET = os.getenv('LINE_CHANNEL_SECRET', '')

print(f"TOKEN: {'OK' if LINE_CHANNEL_ACCESS_TOKEN else 'MISSING'}")
print(f"SECRET: {'OK' if LINE_CHANNEL_SECRET else 'MISSING'}")

# 儲存提醒：{user_id: [{"time": "09:00", "content": "喝水", "last_sent": "2026-03-11"}]}
reminders = {}
# 記錄已發送的提醒（避免重複發送）
sent_today = {}

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

# 定時檢查提醒（供 Vercel Cron 呼叫）
@app.route('/check-reminders', methods=['GET', 'POST'])
def check_reminders():
    """檢查並發送提醒"""
    print("檢查提醒中...")
    now = datetime.now()
    current_time = now.strftime("%H:%M")
    today = now.strftime("%Y-%m-%d")
    
    print(f"目前時間: {current_time}, 日期: {today}")
    
    for user_id, user_reminders in reminders.items():
        for reminder in user_reminders:
            reminder_time = reminder.get('time')
            content = reminder.get('content', '')
            last_sent = reminder.get('last_sent', '')
            
            # 如果時間到了且今天還沒發送
            if reminder_time == current_time and last_sent != today:
                print(f"發送提醒給 {user_id}: {reminder_time} - {content}")
                send_push_message(user_id, f"⏰ 提醒：{content}")
                reminder['last_sent'] = today
    
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
  例：設定提醒 09:00 喝水
• 列出提醒
• 刪除提醒 [編號]
• 清除所有
• 測試提醒 - 測試發送
• 幫助"""
    
    elif text in ["列出提醒", "list"]:
        if user_id in reminders and reminders[user_id]:
            reply_text = "📝 你的提醒：\n"
            for i, r in enumerate(reminders[user_id], 1):
                reply_text += f"{i}. ⏰ {r['time']} - {r['content']}\n"
        else:
            reply_text = "目前沒有設定提醒"
    
    elif text in ["清除所有", "clear"]:
        if user_id in reminders:
            reminders[user_id] = []
        reply_text = "✅ 已清除所有提醒"
    
    elif text in ["測試提醒", "測試"]:
        # 測試發送訊息
        send_push_message(user_id, "✅ 測試訊息成功！")
        reply_text = "已發送測試訊息給你"
    
    elif text.startswith("刪除提醒") or text.startswith("刪除"):
        try:
            parts = text.split()
            if len(parts) >= 2:
                idx = int(parts[1]) - 1
                if user_id in reminders and 0 <= idx < len(reminders[user_id]):
                    deleted = reminders[user_id].pop(idx)
                    reply_text = f"✅ 已刪除：{deleted['time']} - {deleted['content']}"
                else:
                    reply_text = "❌ 無效的編號"
            else:
                reply_text = "請指定編號，如：刪除提醒 1"
        except:
            reply_text = "❌ 請輸入正確編號"
    
    elif text.startswith("設定提醒"):
        import re
        content = text[4:].strip()
        match = re.search(r'(\d{1,2}:\d{2})', content)
        if match:
            time = match.group(1)
            reminder_content = content.replace(time, "").strip()
            if user_id not in reminders:
                reminders[user_id] = []
            reminders[user_id].append({"time": time, "content": reminder_content, "last_sent": ""})
            reply_text = f"✅ 已設定：⏰ {time} - {reminder_content}\n💡 每天時間到了會自動發送提醒給你"
        else:
            reply_text = "❌ 請指定時間，如：設定提醒 09:00 喝水"
    
    else:
        reply_text = "請輸入「幫助」查看指令"
    
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
        r = requests.post(url, headers=headers, json=data, timeout=10)
        print(f"回覆結果: {r.status_code}")
    except Exception as e:
        print(f"回覆錯誤: {e}")

def send_push_message(user_id, text):
    """發送推播訊息"""
    import requests
    
    url = 'https://api.line.me/v2/bot/message/push'
    headers = {
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {LINE_CHANNEL_ACCESS_TOKEN}'
    }
    data = {
        'to': user_id,
        'messages': [{'type': 'text', 'text': text}]
    }
    
    try:
        r = requests.post(url, headers=headers, json=data, timeout=10)
        print(f"推播結果: {r.status_code} - {r.text}")
    except Exception as e:
        print(f"推播錯誤: {e}")

# 本地開發時的背景執行緒
def run_scheduler():
    """本地開發用的定時檢查"""
    import time
    while True:
        with app.test_request_context('/check-reminders'):
            check_reminders()
        time.sleep(60)  # 每分鐘檢查一次

if __name__ == "__main__":
    # 本地開發時啟動定時器
    scheduler_thread = threading.Thread(target=run_scheduler, daemon=True)
    scheduler_thread.start()
    app.run(host="0.0.0.0", port=5000)
