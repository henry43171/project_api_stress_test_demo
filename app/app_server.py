# app/app_server.py
from flask import Flask, jsonify, request
from flasgger import Swagger
import time
import json
import os
import sys
import random

# ----------------------
# 讀取設定檔
# ----------------------
CONFIG_PATH = "config/server_config.json"

if os.path.exists(CONFIG_PATH):
    with open(CONFIG_PATH, "r", encoding="utf-8") as f:
        CONFIG = json.load(f)
else:
    print("無法啟動伺服器：缺少設定檔 config/server_config.json")
    sys.exit(1)

# ----------------------
# 初始化 Flask
# ----------------------
app = Flask(__name__)
swagger = Swagger(app)

# ----------------------
# 計算成功率
# ----------------------
def get_success_probability(current_users):
    t = CONFIG["user_thresholds"]
    base = CONFIG["base_success_rate"]
    min_rate = CONFIG["min_success_rate"]

    if current_users <= t["safe"]:
        return base
    elif current_users >= t["decay_end"]:
        return min_rate
    else:
        ratio = (current_users - t["decay_start"]) / (t["decay_end"] - t["decay_start"])
        return base - (base - min_rate) * ratio


# ----------------------
# GET /landing_page
# ----------------------
@app.route("/landing_page", methods=["GET"])
def landing_page():
    """
    使用者進入首頁，回傳文字提示與模擬媒體預覽
    ---
    responses:
      200:
        description: 首頁資訊
        content:
          application/json:
            example:
              message: "歡迎來到匿名表單填寫系統！"
              media_preview: "模擬圖片/影片大字串...(略)"
    """
    time.sleep(0.5)
    media_preview = "X" * 100000
    return jsonify({
        "message": "歡迎來到匿名表單填寫系統！",
        "media_preview": media_preview[:100] + "...(略)"
    })


# ----------------------
# GET /start_form
# ----------------------
@app.route("/start_form", methods=["GET"])
def start_form():
    """
    使用者點擊「填寫表單」按鈕，回傳空表單結構
    ---
    responses:
      200:
        description: 空表單 JSON 結構
        content:
          application/json:
            example:
              form:
                gender: ""
                age_group: ""
                feedback: ""
                willing:
                  to_return: false
                  receive_promotions: false
                  receive_birthday_notifications: false
    """
    time.sleep(0.2)
    form_structure = {
        "gender": "",
        "age_group": "",
        "feedback": "",
        "willing": {
            "to_return": False,
            "receive_promotions": False,
            "receive_birthday_notifications": False
        }
    }
    return jsonify({"form": form_structure})


# ----------------------
# POST /submit_form
# ----------------------
@app.route("/submit_form", methods=["POST"])
def submit_form():
    """
    使用者送出表單，根據傳入的 current_users 計算成功率
    ---
    requestBody:
      required: true
      content:
        application/json:
          schema:
            type: object
            properties:
              gender:
                type: string
              age_group:
                type: string
              feedback:
                type: string
              willing:
                type: object
                properties:
                  to_return:
                    type: boolean
                  receive_promotions:
                    type: boolean
                  receive_birthday_notifications:
                    type: boolean
              current_users:
                type: integer
          example:
            gender: "male"
            age_group: "20-30"
            feedback: "很好"
            willing:
              to_return: true
              receive_promotions: false
              receive_birthday_notifications: true
            current_users: 150
    responses:
      200:
        description: 表單提交成功
      503:
        description: 伺服器忙碌
    """
    form_data = request.json or {}
    current_users = form_data.get("current_users", CONFIG["user_thresholds"]["safe"])
    success_prob = get_success_probability(current_users)
    time.sleep(0.3)

    if random.random() < success_prob:
        return jsonify({
            "message": f"表單提交成功！（目前模擬使用者 {current_users} 人，成功率 {success_prob:.2f}）",
            "received_form": form_data
        })
    else:
        return jsonify({
            "message": f"伺服器忙碌，請稍後再試。（目前模擬使用者 {current_users} 人，成功率 {success_prob:.2f}）"
        }), 503


if __name__ == "__main__":
    app.run(debug=True)
