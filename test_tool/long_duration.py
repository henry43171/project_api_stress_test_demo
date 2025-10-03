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
# 讀取長時間設定
# ----------------------
LD_CONFIG_PATH = Path("config/long_duration.json")
with open(LD_CONFIG_PATH, "r", encoding="utf-8") as f:
    ld_config = json.load(f)

TEST_TOTAL_TIME = ld_config["test_total_time"]
TEST_UNIT_TIME = ld_config["test_unit_time"]
UNIT_USERS = ld_config.get("unit_users", 10)
PEAKS = ld_config.get("peaks", [])
AMPLITUDE = ld_config.get("amplitude", 0.5)
NOISE = ld_config.get("noise", 0.1)
SUCCESS_THRESHOLDS = ld_config.get("success_thresholds", [0.95, 0.7])
DECAY_RATE = ld_config.get("decay_rate", 0.01)

# ----------------------
# 設定log存放位置
# ----------------------
LOG_DIR = Path("results/logs/long_duration")
SUMMARY_DIR = Path("results/summary/long_duration")
LOG_DIR.mkdir(parents=True, exist_ok=True)
SUMMARY_DIR.mkdir(parents=True, exist_ok=True)

timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
summary_file = SUMMARY_DIR / f"summary_{timestamp}_total{TEST_TOTAL_TIME}_unit{TEST_UNIT_TIME}.json"

# ----------------------
# 工具函式
# ----------------------
def period_user(period_index: int, num_periods: int) -> int:
    """
    人數生成：
    - 基準人數：UNIT_USERS
    - 加上正弦曲線模擬高峰
    - peaks 可提高特定時段的人數
    - noise 加入隨機擾動
    """
    # 基準人數
    base = UNIT_USERS

    # 正弦波調整 (週期 = num_periods)
    angle = (2 * math.pi * period_index) / num_periods
    sine_factor = 1 + AMPLITUDE * math.sin(angle)

    # peaks 額外加權
    peak_bonus = 3 if period_index in PEAKS else 1.0

    # noise 隨機擾動
    noise_factor = 1 + random.uniform(-NOISE, NOISE)

    # 計算人數（至少 1 人）
    users = max(1, int(base * sine_factor * peak_bonus * noise_factor))
    return users


def simulate_success(users: int) -> bool:
    """
    成功率模擬：
    - 根據人數，從高閾值逐漸衰減到低閾值
    - 模型：prob = max(low, high - decay * users)
    """
    high, low = SUCCESS_THRESHOLDS
    prob = max(low, high - DECAY_RATE * users)
    return random.random() < prob


# ----------------------
# 單人流程封裝
# ----------------------
def user_test(index, total_users):
    result = {"user": index, "steps": [], "success": True, "TEST_TOTAL_TIME": 0.0}
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

        result["TEST_TOTAL_TIME"] = time.time() - start_time
    except Exception as e:
        result["success"] = False
        result["error"] = str(e)
    return result


# ----------------------
# 主流程
# ----------------------
def run_long_duration():
    num_periods = TEST_TOTAL_TIME // TEST_UNIT_TIME
    if TEST_TOTAL_TIME % TEST_UNIT_TIME != 0:
        raise ValueError("TEST_TOTAL_TIME 必須能被 TEST_UNIT_TIME 整除")

    all_results = []
    period_stats = []

    for p in range(num_periods):
        users = period_user(p, num_periods)
        period_results = []

        with ThreadPoolExecutor() as executor:
            futures = [executor.submit(user_test, i, users) for i in range(users)]
            for future in as_completed(futures):
                period_results.append(future.result())

        # 單位時間統計
        successes = sum(1 for r in period_results if r["success"])
        avg_time = sum(r["TEST_TOTAL_TIME"] for r in period_results) / len(period_results)
        stat = {
            "period": p,
            "users": users,
            "success_rate": successes / len(period_results),
            "avg_time": avg_time
        }
        period_stats.append(stat)

        # 寫入 log
        log_file = LOG_DIR / f"longrun_{timestamp}_p{p}_users{users}.json"
        with open(log_file, "w", encoding="utf-8") as f:
            json.dump(period_results, f, indent=2, ensure_ascii=False)

        all_results.extend(period_results)
        print(f"[Period {p}] Users={users}, Success={stat['success_rate']:.2f}, AvgTime={avg_time:.2f}s")

    # ----------------------
    # 全域統計
    # ----------------------
    total = len(all_results)
    successes = sum(1 for r in all_results if r["success"])
    avg_time = sum(r["TEST_TOTAL_TIME"] for r in all_results) / total

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
