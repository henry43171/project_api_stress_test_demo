import requests
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
import json
import logging
import random
import os
from datetime import datetime
import math

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

# pass probability
def calculate_pass_probability(num_users, threshold=300, drop_per_user=0.1, noise_frac=0.05):
    """
    極簡分段：
    - num_users <= threshold: pass_rate = 1.0
    - num_users > threshold: pass_rate = max(0.0, 1 - (num_users - threshold) * drop_per_user)
      並加上 +/- noise_frac 隨機波動（相對於計算出的 pass_rate）
    """
    if num_users <= threshold:
        prob = 1.0
    else:
        prob = max(0.0, 1.0 - (num_users - threshold) * drop_per_user)

    # 加上少量相對噪聲
    noise = random.uniform(-noise_frac, noise_frac) * prob
    prob = prob + noise
    return max(0.0, min(prob, 1.0))



def simulate_user(user_id, form_data, current_num_users=NUM_USERS, execute_api=True):
    """
    模擬使用者行為
    - execute_api: False 時不發送 HTTP 請求，只做模擬計算
    """
    start_total = time.time()
    actions_taken = []
    status_codes = []
    filled_form = None
    result = None
    success = True

    pass_probability = calculate_pass_probability(current_num_users, threshold=300)

    if random.random() > pass_probability:
        elapsed_total = random.uniform(0.1, 2.0)
        if execute_api:
            logging.info(
                "User %d - Action: %s, Result: FAIL (simulated due to load), Time: %.2fs",
                user_id, [], elapsed_total
            )
        return {
            "user_id": user_id,
            "actions": [],
            "success": "FAIL",
            "status_codes": [],
            "elapsed": elapsed_total,
            "filled_form": filled_form,
            "result": {"error": "Simulated failure due to load"}
        }

    if not execute_api:
        # 只模擬，不打 API
        elapsed_total = random.uniform(0.5, 2.0)
        action = random.choices(
            [a[0] for a in USER_ACTIONS],
            weights=[a[1] for a in USER_ACTIONS]
        )[0]
        actions_taken.append(action)
        success = True
        status_codes = [200] * len(actions_taken)
        filled_form = {k: form_data[k] for k in ("gender", "age_group", "feedback", "willing")}
        result = {"simulated": True}
        return {
            "user_id": user_id,
            "actions": actions_taken,
            "success": "PASS",
            "status_codes": status_codes,
            "elapsed": elapsed_total,
            "filled_form": filled_form,
            "result": result
        }

    # --- 原本 API 行為模擬 ---
    try:
        action = random.choices(
            [a[0] for a in USER_ACTIONS],
            weights=[a[1] for a in USER_ACTIONS]
        )[0]

        if action in ("visit_home", "fill_form"):
            time.sleep(random.uniform(0.1, 0.5))
            r1 = make_request("GET", f"{BASE_URL}/landing_page")
            status_codes.append(r1.status_code if hasattr(r1, "status_code") else None)
            actions_taken.append("visit_home")
            if getattr(r1, "status_code", 0) != 200:
                success = False

        if action == "fill_form":
            time.sleep(random.uniform(0.1, 0.3))
            r2 = make_request("POST", f"{BASE_URL}/start_form")
            status_codes.append(r2.status_code if hasattr(r2, "status_code") else None)
            actions_taken.append("start_form")
            if getattr(r2, "status_code", 0) != 200:
                success = False

            time.sleep(random.uniform(0.2, 0.7))
            filled_form = {k: form_data[k] for k in ("gender", "age_group", "feedback", "willing")}
            r3 = make_request("POST", f"{BASE_URL}/submit_form", json=filled_form)
            status_codes.append(r3.status_code if hasattr(r3, "status_code") else None)
            actions_taken.append("submit_form")
            if getattr(r3, "status_code", 0) != 200:
                success = False
            result = r3.json() if getattr(r3, "status_code", 0) == 200 else {"error": f"Status code {getattr(r3, 'status_code', 'N/A')}"}

        elif action == "refresh_page":
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

    if execute_api:
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

# --- 主程式 ---
def main():
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_dir = os.path.join("results/logs", "core")
    summary_dir = os.path.join("results/summary", "core")
    os.makedirs(log_dir, exist_ok=True)
    os.makedirs(summary_dir, exist_ok=True)

    log_file = os.path.join(log_dir, f"core_{timestamp}.log")
    summary_file = os.path.join(summary_dir, f"core_{timestamp}_summary.json")

    logging.basicConfig(
        filename=log_file,
        filemode="w",
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(message)s",
        encoding="utf-8"
    )

    results = []
    start_total = time.time()
    forms_to_use = fake_forms[:NUM_USERS]

    for i in range(0, NUM_USERS, BATCH_SIZE):
        batch_forms = forms_to_use[i:i+BATCH_SIZE]
        max_workers = min(len(batch_forms), MAX_WORKERS)
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = [executor.submit(simulate_user, i+j+1, batch_forms[j], current_num_users=NUM_USERS) for j in range(len(batch_forms))]
            for future in as_completed(futures):
                results.append(future.result())
        time.sleep(BATCH_DELAY)

    end_total = time.time()

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

    with open(summary_file, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2, ensure_ascii=False)

    print("\n--- Test Summary ---")
    print(json.dumps(summary, indent=2, ensure_ascii=False))
    print(f"\nSummary saved to: {summary_file}")
    print(f"Log saved to: {log_file}")


if __name__ == "__main__":
    main()
