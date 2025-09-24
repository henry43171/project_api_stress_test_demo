import json
import random

def generate_fake_data(num_records=100, foldername = "fake_data", filename="fake_form_data.json"):
    """
    產生包含性別、年齡、回饋等隨機資料的 JSON 檔案。

    Args:
        num_records (int): 欲產生的資料筆數。預設為 100 筆。
        filename (str): 輸出的 JSON 檔案名稱。預設為 "fake_form_data.json"。
    """
    genders = ["male", "female", "other"]
    age_groups = ["10以下", "10-20", "20-30", "30-40", "40-50", "50-60", "60-70", "70以上"]
    feedback_samples = ["非常滿意", "很好", "一般", "不錯", "需要改進"]

    data = []
    for _ in range(num_records):
        record = {
            "gender": random.choice(genders),
            "age_group": random.choice(age_groups),
            "feedback": random.choice(feedback_samples),
            "willing": {
                "to_return": random.choice([True, False]),
                "receive_promotions": random.choice([True, False]),
                "receive_birthday_notifications": random.choice([True, False])
            }
        }
        data.append(record)

    # 確保資料夾存在
    import os
    os.makedirs(foldername, exist_ok=True)

    file_path = os.path.join(foldername, filename)
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

    print(f"成功產生 {num_records} 筆資料，並儲存至 {file_path}")

# 範例使用方式：
# 1. 使用預設值（產生 100 筆資料，檔名為 fake_form_data.json）
num_records = 100
foldername = "fake_data"
filename="fake_form_data.json"

generate_fake_data(num_records=num_records, foldername=foldername, filename=filename)
