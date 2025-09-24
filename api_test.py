import requests
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
import json
import logging

BASE_URL = "http://127.0.0.1:5000"
NUM_USERS = 10000  # 模擬使用者數量

# Logging 設定
logging.basicConfig(
    filename="api_test.log",
    filemode="w",   # 每次跑覆蓋
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    encoding="utf-8"   # 中文編碼
)

# 讀取假資料作為表單填寫內容
with open("./fake_data/fake_form_data.json", "r", encoding="utf-8") as f:
    fake_forms = json.load(f)

def simulate_user(user_id, form_data):
    start_time = time.time()
    success = True
    status_codes = []
    filled_form = None  # 先宣告，避免 exception 時未定義
    result = None

    try:
        # 1. 進入首頁
        r1 = requests.get(f"{BASE_URL}/landing_page")
        status_codes.append(r1.status_code)
        if r1.status_code != 200:
            success = False

        # 2. 開始填寫表單
        r2 = requests.post(f"{BASE_URL}/start_form")
        status_codes.append(r2.status_code)
        if r2.status_code != 200:
            success = False

        # 3. 填入假資料中的表單並送出
        filled_form = {
            "gender": form_data["gender"],
            "age_group": form_data["age_group"],
            "feedback": form_data["feedback"],
            "willing": form_data["willing"]
        }
        r3 = requests.post(f"{BASE_URL}/submit_form", json=filled_form)
        status_codes.append(r3.status_code)
        if r3.status_code != 200:
            success = False

        if r3.status_code == 200:
            result = r3.json()
        else:
            result = {"error": f"Status code {r3.status_code}"}

    except Exception as e:
        success = False
        result = {"error": str(e)}

    end_time = time.time()
    elapsed = end_time - start_time

    # 寫 log（即使 filled_form 為 None 也能寫入）
    logging.info(
        "User %d - Success: %s, Time: %.2fs, Status: %s, Payload: %s, Result: %s",
        user_id, success, elapsed, status_codes, filled_form if filled_form else {}, result if result else {}
    )

    return {
        "user_id": user_id,
        "success": success,
        "status_codes": status_codes,
        "elapsed": elapsed,
        "filled_form": filled_form,
        "result": result
    }

def main():
    results = []
    start_total = time.time()

    forms_to_use = fake_forms[:NUM_USERS]

    # ThreadPoolExecutor 控制最大併發數量，避免爆掉系統
    max_workers = min(NUM_USERS, 200)  # 可調整，避免同時啟動過多 thread
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = [executor.submit(simulate_user, i+1, forms_to_use[i]) for i in range(NUM_USERS)]
        for future in as_completed(futures):
            results.append(future.result())

    end_total = time.time()

    # 統計
    total_success = sum(1 for r in results if r["success"])
    total_fail = NUM_USERS - total_success
    avg_time = sum(r["elapsed"] for r in results) / len(results)
    max_time = max(r["elapsed"] for r in results)

    print("\n--- Test Summary ---")
    print(f"Total users: {NUM_USERS}")
    print(f"Success: {total_success}, Fail: {total_fail}")
    print(f"Average response time: {avg_time:.2f}s")
    print(f"Max response time: {max_time:.2f}s")
    print(f"Total test duration: {end_total - start_total:.2f}s")

    # Console 顯示部分結果
    for r in results[:5]:
        print(f"User {r['user_id']} - Success: {r['success']}, Time: {r['elapsed']:.2f}s, Status: {r['status_codes']}")

if __name__ == "__main__":
    main()
