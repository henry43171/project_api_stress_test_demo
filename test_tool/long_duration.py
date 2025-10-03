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
LOW_BENCHMRK = ld_config.get("low_benchmark", 10)
HIGH_BENCHMRK = ld_config.get("high_benchmark", 50)
PEAKS = ld_config.get("peaks", [2, 6])
PEAK_SCALE = ld_config.get("peak_scale", 4.0)   # 高峰倍數
AMPLITUDE = ld_config.get("amplitude", 0.5)
NOISE = ld_config.get("noise", 0.008)
SUCCESS_THRESHOLDS = ld_config.get("success_thresholds", [1.0, 0.6])
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
# ---- 人數生成函式 ----
def period_user(period_index: int, num_periods: int) -> int:
    """
    Gaussian 平滑峰值 + 可調整最大倍數
    """
    base = UNIT_USERS
    noise_factor = 1 + random.uniform(-NOISE, NOISE)

    peak_factor = 0.0
    for peak in PEAKS:
        sigma = 3
        distance = period_index - peak
        peak_factor += math.exp(-(distance**2) / (2 * sigma**2))  # 最大值 1

    # scale 高峰，最大 users = base * PEAK_SCALE
    users = max(1, int(base * (1 + (PEAK_SCALE - 1) * peak_factor) * noise_factor))
    return users

def simulate_success(users: int,
                     success_thresholds: list =SUCCESS_THRESHOLDS,
                     low_benchmark: int = LOW_BENCHMRK,
                     high_benchmark: int = HIGH_BENCHMRK) -> float:
    """
    模擬成功率，分段控制：
    - users <= low_benchmark → 最大成功率
    - low_benchmark < users <= high_benchmark → 線性衰減
    - users > high_benchmark → 最小成功率

    參數：
    - users: 當前人數
    - success_thresholds: (高閾值, 低閾值)
    - low_benchmark: 線性衰減起點
    - high_benchmark: 線性衰減終點
    """
    high, low = success_thresholds

    if users <= low_benchmark:
        return high
    elif users <= high_benchmark:
        # 線性衰減公式，保證不低於 low
        prob = high * (1 - (users - low_benchmark) / (high_benchmark - low_benchmark))
        return max(prob, low)
    else:
        return low


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
            prob = simulate_success(total_users)
            step_success = r.status_code == 200 and (random.random() < prob)
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
        print(f"[Period {p+1}/{num_periods}] Users={users}, Success={stat['success_rate']:.2f}, AvgTime={avg_time:.2f}s")

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
