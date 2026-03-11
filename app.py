"""
LINE 每日提醒機器人
功能：設定和管理每日定時提醒
"""

from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.models import MessageEvent, TextMessage, TextSendMessage, TemplateSendMessage, ButtonsTemplate, MessageAction
from datetime import datetime, time
import os
import json

app = Flask(__name__)

# 環境變數
LINE_CHANNEL_ACCESS_TOKEN = os.getenv("LINE_CHANNEL_ACCESS_TOKEN", "")
LINE_CHANNEL_SECRET = os.getenv("LINE_CHANNEL_SECRET", "")

line_bot_api = LineBotApi(LINE_CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(LINE_CHANNEL_SECRET)

# 儲存提醒資料（正式環境應使用資料庫）
reminders = {}

@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    user_id = event.source.user_id
    text = event.message.text.strip()
    
    # 幫助指令
    if text in ["help", "幫助", "?"]:
        help_text = """📋 LINE 每日提醒機器人

可用指令：
• 設定提醒 [時間] [內容] - 新增提醒
  例：設定提醒 09:00 喝水
• 列出提醒 - 查看所有提醒
• 刪除提醒 [編號] - 刪除提醒
• 清除所有 - 刪除所有提醒
• 幫助 - 顯示此訊息"""
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
    if text in ["清除所有", "clear", "刪除全部"]:
        if user_id in reminders:
            reminders[user_id] = []
        line_bot_api.reply_message(event.reply_token, TextSendMessage(text="✅ 已清除所有提醒"))
        return
    
    # 刪除單一提醒
    if text.startswith("刪除提醒") or text.startswith("刪除"):
        try:
            parts = text.split()
            if len(parts) >= 2:
                idx = int(parts[1]) - 1
                if user_id in reminders and 0 <= idx < len(reminders[user_id]):
                    deleted = reminders[user_id].pop(idx)
                    line_bot_api.reply_message(event.reply_token, 
                        TextSendMessage(text=f"✅ 已刪除提醒：{deleted['time']} - {deleted['content']}"))
                else:
                    line_bot_api.reply_message(event.reply_token, 
                        TextSendMessage(text="❌ 無效的編號"))
            else:
                line_bot_api.reply_message(event.reply_token, 
                    TextSendMessage(text="請指定編號，如：刪除提醒 1"))
        except ValueError:
            line_bot_api.reply_message(event.reply_token, 
                TextSendMessage(text="❌ 請輸入正確的編號"))
        return
    
    # 設定提醒
    if text.startswith("設定提醒") or text.startswith("提醒"):
        try:
            # 解析指令
            if text.startswith("設定提醒"):
                content = text[4:].strip()  # 移除 "設定提醒"
            else:
                content = text[2:].strip()  # 移除 "提醒"
            
            # 尋找時間（格式：HH:MM）
            import re
            time_match = re.search(r'(\d{1,2}:\d{2})', content)
            
            if not time_match:
                line_bot_api.reply_message(event.reply_token, 
                    TextSendMessage(text="❌ 請指定時間，格式：設定提醒 09:00 喝水"))
                return
            
            time_str = time_match.group(1)
            reminder_content = content.replace(time_str, "").strip()
            
            if not reminder_content:
                line_bot_api.reply_message(event.reply_token, 
                    TextSendMessage(text="❌ 請指定提醒內容，如：設定提醒 09:00 喝水"))
                return
            
            # 儲存提醒
            if user_id not in reminders:
                reminders[user_id] = []
            
            reminders[user_id].append({
                "time": time_str,
                "content": reminder_content,
                "created_at": datetime.now().isoformat()
            })
            
            line_bot_api.reply_message(event.reply_token, 
                TextSendMessage(text=f"✅ 已設定提醒：⏰ {time_str} - {reminder_content}"))
            
        except Exception as e:
            line_bot_api.reply_message(event.reply_token, 
                TextSendMessage(text=f"❌ 設定失敗：{str(e)}"))
        return
    
    # 預設回覆
    line_bot_api.reply_message(event.reply_token, 
        TextSendMessage(text="我不知道這個指令，請輸入「幫助」查看可用指令"))

@app.route("/callback", methods=['POST'])
def callback():
    signature = request.headers.get('X-Line-Signature')
    body = request.get_data(as_text=True)
    
    try:
        handler.handle(body, signature)
    except Exception as e:
        print(f"Error: {e}")
        abort(400)
    
    return 'OK'

@app.route("/")
def home():
    return "LINE Bot is running!"

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
