import requests
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
import json

BASE_URL = "http://127.0.0.1:5000"
NUM_USERS = 50  # 模擬使用者數量

# 讀取假資料作為表單填寫內容
with open("./fake_data/fake_form_data.json", "r", encoding="utf-8") as f:
    fake_forms = json.load(f)

def simulate_user(user_id, form_data):
    start_time = time.time()
    
    # 1. 進入首頁
    requests.get(f"{BASE_URL}/landing_page")
    
    # 2. 開始填寫表單
    requests.post(f"{BASE_URL}/start_form")
    
    # 3. 填入假資料中的表單
    filled_form = {
        "gender": form_data["gender"],
        "age_group": form_data["age_group"],
        "feedback": form_data["feedback"],
        "willing": form_data["willing"]
    }
    
    # 4. 送出表單
    r_submit = requests.post(f"{BASE_URL}/submit_form", json=filled_form).json()
    
    end_time = time.time()
    elapsed = end_time - start_time
    
    return user_id, r_submit, elapsed

def main():
    results = []
    start_total = time.time()
    
    # 避免超出假資料長度，取前 NUM_USERS 筆
    forms_to_use = fake_forms[:NUM_USERS]
    
    with ThreadPoolExecutor(max_workers=NUM_USERS) as executor:
        futures = [executor.submit(simulate_user, i+1, forms_to_use[i]) for i in range(NUM_USERS)]
        for future in as_completed(futures):
            user_id, r_submit, elapsed = future.result()
            print(f"User {user_id} result: {r_submit}, time: {elapsed:.2f}s")
            results.append((user_id, r_submit, elapsed))
    
    end_total = time.time()
    print(f"\nTotal time for {NUM_USERS} users: {end_total - start_total:.2f} seconds")

if __name__ == "__main__":
    main()
