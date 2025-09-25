import requests
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
import json
import logging
import random
import os
from datetime import datetime

# --- 讀取 config ---
with open("config/core.json", "r", encoding="utf-8") as f:
    config = json.load(f)

BASE_URL = config.get("BASE_URL", "http://127.0.0.1:5000")
NUM_USERS = config.get("NUM_USERS", 50)
BATCH_SIZE = config.get("BATCH_SIZE", 20)
BATCH_DELAY = config.get("BATCH_DELAY", 1)
MAX_RETRIES = config.get("MAX_RETRIES", 2)
MAX_WORKERS = config.get("MAX_WORKERS", 200)
USER_ACTIONS = [(a["action"], a["weight"]) for a in config.get("USER_ACTIONS", [])]

# --- 建立目錄 & 檔名 ---
timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
log_dir = os.path.join("logs", "core")
summary_dir = os.path.join("summary", "core")
os.makedirs(log_dir, exist_ok=True)
os.makedirs(summary_dir, exist_ok=True)

log_file = os.path.join(log_dir, f"core_{timestamp}.log")
summary_file = os.path.join(summary_dir, f"core_{timestamp}_summary.json")

# --- Logging 設定 ---
logging.basicConfig(
    filename=log_file,
    filemode="w",
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    encoding="utf-8"
)

# --- 讀取假資料 ---
with open("./fake_data/fake_form_data.json", "r", encoding="utf-8") as f:
    fake_forms = json.load(f)

# --- 輔助函數 ---
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

# --- 主程式 (保留原有測試功能) ---
def main():
    results = []
    start_total = time.time()
    forms_to_use = fake_forms[:NUM_USERS]

    for i in range(0, NUM_USERS, BATCH_SIZE):
        batch_forms = forms_to_use[i:i+BATCH_SIZE]
        max_workers = min(len(batch_forms), MAX_WORKERS)
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

    summary = {
        "timestamp": timestamp,
        "total_users": NUM_USERS,
        "pass": total_success,
        "fail": total_fail,
        "avg_response_time": avg_time,
        "max_response_time": max_time,
        "total_test_duration": end_total - start_total,
        "stage_avg_times": {
            stage: (sum(times) / len(times) if times else None)
            for stage, times in stage_times.items()
        }
    }

    # 輸出 JSON summary
    with open(summary_file, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2, ensure_ascii=False)

    print("\n--- Test Summary ---")
    print(json.dumps(summary, indent=2, ensure_ascii=False))
    print(f"\nSummary saved to: {summary_file}")
    print(f"Log saved to: {log_file}")

if __name__ == "__main__":
    main()
