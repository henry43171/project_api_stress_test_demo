from flask import Flask, jsonify, request
from flasgger import Swagger
import time

app = Flask(__name__)
swagger = Swagger(app)

# ----------------------
# GET /landing_page
# ----------------------
@app.route("/landing_page", methods=["GET"])
def landing_page():
    """
    模擬使用者進入首頁，回傳文字提示和模擬媒體延遲
    ---
    responses:
      200:
        description: 首頁資訊
        content:
          application/json:
            example:
              message: "歡迎來到匿名表單填寫系統！"
              media_preview: "模擬圖片/影片大字串..."
    """
    time.sleep(0.5)
    media_preview = "X" * 100000
    return jsonify({
        "message": "歡迎來到匿名表單填寫系統！",
        "media_preview": media_preview[:100] + "...(略)"
    })


# ----------------------
# POST /start_form
# ----------------------
@app.route("/start_form", methods=["POST"])
def start_form():
    """
    使用者點擊「填寫表單」按鈕，回傳空表單
    ---
    responses:
      200:
        description: 空表單結構
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
    使用者送出表單，回傳成功訊息
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
          example:
            gender: "male"
            age_group: "20-30"
            feedback: "很好"
            willing:
              to_return: true
              receive_promotions: false
              receive_birthday_notifications: true
    responses:
      200:
        description: 表單提交成功
        content:
          application/json:
            example:
              message: "表單提交成功！"
              received_form:
                gender: "male"
                age_group: "20-30"
                feedback: "很好"
                willing:
                  to_return: true
                  receive_promotions: false
                  receive_birthday_notifications: true
    """
    form_data = request.json
    time.sleep(0.3)
    return jsonify({
        "message": "表單提交成功！",
        "received_form": form_data
    })


if __name__ == "__main__":
    app.run(debug=True)
