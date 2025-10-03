# test_tool/high_concurrency.py
import os
import json
import time
import random
from pathlib import Path
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
from core.api_test_core import visit_landing_page, start_form, submit_form
import logging

# ----------------------
# 讀取假資料
# ----------------------
FAKE_DATA_PATH = Path("fake_data/fake_form_data.json")
with open(FAKE_DATA_PATH, "r", encoding="utf-8") as f:
    fake_data_list = json.load(f)

data = fake_data_list[0]

# ----------------------
# 讀取高併發設定
# ----------------------
HC_CONFIG_PATH = Path("config/high_concurrency.json")
with open(HC_CONFIG_PATH, "r", encoding="utf-8") as f:
    hc_config = json.load(f)

NUM_USERS_LIST = hc_config.get("num_users", [10, 20, 30, 40, 50])
SUCCESS_THRESHOLDS = tuple(hc_config.get("success_thresholds", [30, 50]))
DECAY_RATE = hc_config.get("decay_rate", 0.7)

# ----------------------
# 設定log存放位置
# ----------------------
LOG_DIR = Path("results/logs/high_concurrency")
LOG_DIR.mkdir(parents=True, exist_ok=True)
SUMMARY_DIR = Path("results/summary/high_concurrency")
SUMMARY_DIR.mkdir(parents=True, exist_ok=True)

# ----------------------
# 成功率模擬
# ----------------------
def simulate_success(n, thresholds=SUCCESS_THRESHOLDS, decay=DECAY_RATE):
    if n <= thresholds[0]:
        return True
    elif thresholds[0] < n <= thresholds[1]:
        return random.random() < decay ** (n - thresholds[0])
    else:
        return random.random() < 0.1

# ----------------------
# 單一用戶測試封裝
# ----------------------
def user_test(index, total_users):
    result = {"user": index, "steps": [], "success": True, "total_time": 0.0}
    start_time = time.time()
    try:
        for step_name, func in [("landing_page", visit_landing_page),
                                ("start_form", start_form),
                                ("submit_form", lambda: submit_form(data))]:
            r, elapsed = func()
            step_success = r.status_code == 200 and simulate_success(total_users)
            result["steps"].append({"step": step_name, "success": step_success, "time": elapsed})
            if not step_success:
                result["success"] = False

        result["total_time"] = time.time() - start_time

    except Exception as e:
        result["success"] = False
        result["error"] = str(e)

    return result

# ----------------------
# 高併發執行
# ----------------------
def run_high_concurrency():
    for NUM_USERS in NUM_USERS_LIST:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        log_file = LOG_DIR / f"hc_{NUM_USERS}u_{timestamp}.log"

        # 設定 logger
        logger = logging.getLogger(f"hc_{NUM_USERS}")
        logger.setLevel(logging.INFO)
        logger.handlers.clear()  # 避免重複
        fh = logging.FileHandler(log_file, mode='w', encoding='utf-8')
        formatter = logging.Formatter('%(asctime)s | %(levelname)s | %(message)s')
        fh.setFormatter(formatter)
        logger.addHandler(fh)

        logger.info(f"Start high concurrency test: {NUM_USERS} users")

        results = []
        with ThreadPoolExecutor(max_workers=NUM_USERS) as executor:
            futures = [executor.submit(user_test, i+1, NUM_USERS) for i in range(NUM_USERS)]
            for future in as_completed(futures):
                res = future.result()
                results.append(res)
                logger.info(f"User {res['user']} finished, success: {res['success']}, total_time: {res['total_time']:.3f}s")

        # ----------------------
        # 統計計算
        # ----------------------
        total = len(results)
        success_count = sum(1 for r in results if r["success"])
        fail_count = total - success_count
        avg_time = sum(r["total_time"] for r in results) / total if total else 0.0

        # 步驟級別統計
        step_stats = {}
        for step_name in ["landing_page", "start_form", "submit_form"]:
            step_times = [s["time"] for r in results for s in r["steps"] if s["step"] == step_name]
            step_success = [s["success"] for r in results for s in r["steps"] if s["step"] == step_name]
            step_stats[step_name] = {
                "average_time": sum(step_times)/len(step_times) if step_times else 0.0,
                "success_rate": sum(step_success)/len(step_success) if step_success else 0.0
            }

        summary = {
            "NUM_USERS": NUM_USERS,
            "total_users": total,
            "success_count": success_count,
            "fail_count": fail_count,
            "success_rate": success_count / total if total else 0.0,
            "average_time": avg_time,
            "step_stats": step_stats
        }

        logger.info(f"SUMMARY: {summary}")

        # 存放 summary JSON
        summary_file = SUMMARY_DIR / f"summary_{NUM_USERS}u_{timestamp}.json"
        with open(summary_file, "w", encoding="utf-8") as f:
            json.dump(summary, f, indent=2)

        print(f"----------------- High concurrency test for {NUM_USERS} users finished -----------------")
        print(f"Log: {log_file}")
        print(f"Summary: {summary_file}\n")

if __name__ == "__main__":
    run_high_concurrency()
