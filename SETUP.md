# 🚀 LINE 每日提醒機器人 - 安裝指南

## 前置需求
- Python 3.8+
- LINE Developer 帳號

## 安裝步驟

### 1. 建立 LINE Bot
1. 前往 [LINE Developers Console](https://developers.line.biz/)
2. 建立新 Provider
3. 建立新 Channel (Messaging API)
4. 取得 Channel Access Token 和 Channel Secret

### 2. 設定環境
```bash
# 複製環境變數範例
cp .env.example .env

# 編輯 .env，填入你的 LINE Bot 資訊
```

### 3. 安裝依賴
```bash
pip install -r requirements.txt
```

### 4. 啟動機器人
```bash
python app.py
```

### 5. 設定 Webhook
1. 在 LINE Developers Console 設定 Webhook URL：
   `https://your-domain.com/callback`
2. 開啟 "Use webhook" 功能

## 使用指令

| 指令 | 說明 |
|------|------|
| 設定提醒 09:00 喝水 | 新增每日提醒 |
| 列出提醒 | 查看所有提醒 |
| 刪除提醒 1 | 刪除第 1 個提醒 |
| 清除所有 | 刪除所有提醒 |
| 幫助 | 顯示指令列表 |

## 部署建議
- Render / Railway / Heroku（免費部署）
- 使用 ngrok 測試本地開發

---
Made with ❤️
