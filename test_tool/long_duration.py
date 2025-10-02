# test_tool/long_duration.py
import os
import json
import time
import random
import math
from pathlib import Path
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
from core.api_test_core import visit_landing_page, start_form, submit_form

# ----------------------
# 假資料
# ----------------------
FAKE_DATA_PATH = Path("fake_data/fake_form_data.json")
with open(FAKE_DATA_PATH, "r", encoding="utf-8") as f:
    fake_data_list = json.load(f)
data = fake_data_list[0]

# ----------------------
# 長時間設定
# ----------------------
LD_CONFIG_PATH = Path("config/long_duration.json")
with open(LD_CONFIG_PATH, "r", encoding="utf-8") as f:
    cfg = json.load(f)

TOTAL_TIME = cfg["total_time"]
UNIT_TIME = cfg["unit_time"]
UNIT_USERS = cfg.get("unit_users", 10)
PEAKS = cfg.get("peaks", [])
AMPLITUDE = cfg.get("amplitude", 0.5)
NOISE = cfg.get("noise", 0.1)
SUCCESS_THRESHOLDS = cfg.get("success_thresholds", [0.95, 0.7])
DECAY_RATE = cfg.get("decay_rate", 0.01)

# ----------------------
# 檔案路徑
# ----------------------
LOG_DIR = Path("results/logs/long_duration")
SUMMARY_DIR = Path("results/summary/long_duration")
LOG_DIR.mkdir(parents=True, exist_ok=True)
SUMMARY_DIR.mkdir(parents=True, exist_ok=True)

timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
summary_file = SUMMARY_DIR / f"summary_{timestamp}_total{TOTAL_TIME}_unit{UNIT_TIME}.json"

# ----------------------
# 工具函式
# ----------------------
def generate_load_ratios(num_periods, peaks, amplitude, noise):
    ratios = []
    for t in range(num_periods):
        base = 1.0 + amplitude * math.sin(2 * math.pi * t / num_periods)
        if t in peaks:
            base *= 1.5
        jitter = random.uniform(-noise, noise)
        ratios.append(max(0.1, base + jitter))
    return ratios

def simulate_success(users, thresholds=SUCCESS_THRESHOLDS, decay=DECAY_RATE):
    high, low = thresholds
    prob = max(low, high - decay * users)
    return random.random() < prob

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
# 主流程
# ----------------------
def run_long_duration():
    if TOTAL_TIME % UNIT_TIME != 0:
        raise ValueError("total_time 必須能被 unit_time 整除")

    num_periods = TOTAL_TIME // UNIT_TIME
    ratios = generate_load_ratios(num_periods, PEAKS, AMPLITUDE, NOISE)

    all_results = []
    period_stats = []

    for period, ratio in enumerate(ratios, start=1):
        num_users = int(UNIT_USERS * ratio)
        period_results = []

        log_file = LOG_DIR / f"longrun_{timestamp}_total{TOTAL_TIME}_unit{UNIT_TIME}_p{period:02d}.log"

        with ThreadPoolExecutor(max_workers=num_users) as executor:
            futures = [executor.submit(user_test, i, num_users) for i in range(num_users)]
            for f in as_completed(futures):
                res = f.result()
                period_results.append(res)

        # 儲存該 period 的 log
        with open(log_file, "w", encoding="utf-8") as f:
            for res in period_results:
                f.write(json.dumps(res, ensure_ascii=False) + "\n")

        # 計算 period 統計
        successes = sum(1 for r in period_results if r["success"])
        avg_time = sum(r["total_time"] for r in period_results) / max(1, len(period_results))
        success_rate = successes / max(1, len(period_results))

        period_stats.append({
            "period": period,
            "users": num_users,
            "success_rate": success_rate,
            "avg_time": avg_time
        })

        all_results.extend(period_results)
        print(f"[Period {period}/{num_periods}] Users={num_users}, Success={success_rate:.2f}, AvgTime={avg_time:.2f}")

        time.sleep(UNIT_TIME)

    # ----------------------
    # 全域統計
    # ----------------------
    total = len(all_results)
    successes = sum(1 for r in all_results if r["success"])
    avg_time = sum(r["total_time"] for r in all_results) / total

    summary = {
        "total_users": total,
        "success_rate": successes / total,
        "avg_time": avg_time,
        "period_stats": period_stats
    }

    with open(summary_file, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2, ensure_ascii=False)

    print(f"----------------- Long duration test finished -----------------")
    print(f"Summary: {summary_file}\n")

if __name__ == "__main__":
    run_long_duration()
