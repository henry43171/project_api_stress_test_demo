import requests
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
import json
import logging
import random

BASE_URL = "http://127.0.0.1:5000"
NUM_USERS = 50
BATCH_SIZE = 20
BATCH_DELAY = 1
MAX_RETRIES = 2

# 行為權重設定
USER_ACTIONS = [
    ("visit_home", 0.5),
    ("fill_form", 0.4),
    ("refresh_page", 0.1)
]

# Logging 設定
logging.basicConfig(
    filename="test_core_upgrade.log",
    filemode="w",
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    encoding="utf-8"
)

# 讀取假資料
with open("./fake_data/fake_form_data.json", "r", encoding="utf-8") as f:
    fake_forms = json.load(f)

def make_request(method, url, **kwargs):
    """帶重試的請求"""
    for attempt in range(MAX_RETRIES + 1):
        try:
            r = requests.request(method, url, **kwargs)
            return r
        except Exception as e:
            if attempt < MAX_RETRIES:
                time.sleep(random.uniform(0.2, 0.5))
            else:
                return {"error": str(e)}

def simulate_user(user_id, form_data):
    start_total = time.time()
    actions_taken = []
    status_codes = []
    filled_form = None
    result = None
    success = True

    # 選擇行為
    action = random.choices(
        [a[0] for a in USER_ACTIONS],
        weights=[a[1] for a in USER_ACTIONS]
    )[0]

    try:
        if action in ("visit_home", "fill_form"):
            # 進入首頁
            time.sleep(random.uniform(0.1, 0.5))
            r1 = make_request("GET", f"{BASE_URL}/landing_page")
            status_codes.append(r1.status_code if hasattr(r1, "status_code") else None)
            actions_taken.append("visit_home")
            if getattr(r1, "status_code", 0) != 200:
                success = False

        if action == "fill_form":
            # 開始表單
            time.sleep(random.uniform(0.1, 0.3))
            r2 = make_request("POST", f"{BASE_URL}/start_form")
            status_codes.append(r2.status_code if hasattr(r2, "status_code") else None)
            actions_taken.append("start_form")
            if getattr(r2, "status_code", 0) != 200:
                success = False

            # 填寫表單
            time.sleep(random.uniform(0.2, 0.7))
            filled_form = {
                "gender": form_data["gender"],
                "age_group": form_data["age_group"],
                "feedback": form_data["feedback"],
                "willing": form_data["willing"]
            }
            r3 = make_request("POST", f"{BASE_URL}/submit_form", json=filled_form)
            status_codes.append(r3.status_code if hasattr(r3, "status_code") else None)
            actions_taken.append("submit_form")
            if getattr(r3, "status_code", 0) != 200:
                success = False
            if getattr(r3, "status_code", 0) == 200:
                result = r3.json()
            else:
                result = {"error": f"Status code {getattr(r3, 'status_code', 'N/A')}"}

        elif action == "refresh_page":
            # 只刷新首頁
            time.sleep(random.uniform(0.1, 0.3))
            r = make_request("GET", f"{BASE_URL}/landing_page")
            status_codes.append(r.status_code if hasattr(r, "status_code") else None)
            actions_taken.append("refresh_page")
            if getattr(r, "status_code", 0) != 200:
                success = False

    except Exception as e:
        success = False
        result = {"error": str(e)}

    elapsed_total = time.time() - start_total

    # log
    logging.info(
        "User %d - Action: %s, Result: %s, Time: %.2fs, Status: %s, Payload: %s, Response: %s",
        user_id, actions_taken, "PASS" if success else "FAIL",
        elapsed_total, status_codes,
        filled_form if filled_form else {},
        result if result else {}
    )

    return {
        "user_id": user_id,
        "actions": actions_taken,
        "success": "PASS" if success else "FAIL",
        "status_codes": status_codes,
        "elapsed": elapsed_total,
        "filled_form": filled_form,
        "result": result
    }

def main():
    results = []
    start_total = time.time()
    forms_to_use = fake_forms[:NUM_USERS]

    for i in range(0, NUM_USERS, BATCH_SIZE):
        batch_forms = forms_to_use[i:i+BATCH_SIZE]
        max_workers = min(len(batch_forms), 200)
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = [executor.submit(simulate_user, i+j+1, batch_forms[j]) for j in range(len(batch_forms))]
            for future in as_completed(futures):
                results.append(future.result())
        time.sleep(BATCH_DELAY)

    end_total = time.time()

    # 分階段統計
    stage_times = {"visit_home": [], "start_form": [], "submit_form": [], "refresh_page": []}
    for r in results:
        for act in r["actions"]:
            stage_times[act].append(r["elapsed"])

    total_success = sum(1 for r in results if r["success"] == "PASS")
    total_fail = NUM_USERS - total_success
    avg_time = sum(r["elapsed"] for r in results) / len(results)
    max_time = max(r["elapsed"] for r in results)

    print("\n--- Test Summary ---")
    print(f"Total users: {NUM_USERS}")
    print(f"PASS: {total_success}, FAIL: {total_fail}")
    print(f"Average response time: {avg_time:.2f}s")
    print(f"Max response time: {max_time:.2f}s")
    print(f"Total test duration: {end_total - start_total:.2f}s")
    print("\nStage average times (s):")
    for stage, times in stage_times.items():
        if times:
            print(f"{stage}: {sum(times)/len(times):.2f}s")

    # Console 顯示部分結果
    for r in results[:5]:
        print(
            f"User {r['user_id']} - Actions: {r['actions']}, "
            f"Result: {r['success']}, "
            f"Time: {r['elapsed']:.2f}s, Status: {r['status_codes']}"
        )

if __name__ == "__main__":
    main()
