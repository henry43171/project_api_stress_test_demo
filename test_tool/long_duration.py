import os
import time
import json
import math
import csv
from datetime import datetime, timedelta
from concurrent.futures import ThreadPoolExecutor, as_completed

from core.api_test_core import simulate_user, fake_forms, BATCH_SIZE, BATCH_DELAY

# 載入設定檔
with open("config/long_duration.json", "r", encoding="utf-8") as f:
    cfg = json.load(f)

DURATION_MINUTES = cfg["DURATION_MINUTES"]
UNIT_INTERVAL_SEC = cfg["UNIT_INTERVAL_SEC"]
USERS_PER_INTERVAL = cfg["USERS_PER_INTERVAL"]
MAX_WORKERS = cfg["MAX_WORKERS"]

# 檔案/資料夾結構 (維持硬編碼)
LOG_DIR = "logs/long_duration"
SUMMARY_DIR = "summary/long_duration"
os.makedirs(LOG_DIR, exist_ok=True)
os.makedirs(SUMMARY_DIR, exist_ok=True)

def run_long_duration_test():
    total_intervals = math.ceil(DURATION_MINUTES * 60 / UNIT_INTERVAL_SEC)
    interval_count = 0
    all_results = []

    while interval_count < total_intervals:
        interval_count += 1
        print(f"({interval_count}/{total_intervals}) Running long duration test interval, simulating {USERS_PER_INTERVAL} users...")

        results = []
        forms_to_use = fake_forms[:USERS_PER_INTERVAL]

        # 分批次
        for i in range(0, USERS_PER_INTERVAL, BATCH_SIZE):
            batch_forms = forms_to_use[i:i+BATCH_SIZE]
            max_workers = min(len(batch_forms), MAX_WORKERS)
            with ThreadPoolExecutor(max_workers=max_workers) as executor:
                futures = [executor.submit(simulate_user, i+j+1, batch_forms[j]) for j in range(len(batch_forms))]
                for future in as_completed(futures):
                    results.append(future.result())
            time.sleep(BATCH_DELAY)

        all_results.extend(results)

        # 統計本 interval
        total_pass = sum(1 for r in results if r["success"] == "PASS")
        total_fail = USERS_PER_INTERVAL - total_pass
        avg_time = sum(r["elapsed"] for r in results) / len(results)
        max_time = max(r["elapsed"] for r in results)
        stage_times = {"visit_home": [], "start_form": [], "submit_form": [], "refresh_page": []}
        for r in results:
            for act in r["actions"]:
                stage_times[act].append(r["elapsed"])
        stage_avg_times = {stage: (sum(times)/len(times) if times else None) for stage, times in stage_times.items()}

        # 檔名時間
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        log_file = os.path.join(LOG_DIR, f"ld_{timestamp}.log")
        summary_file_json = os.path.join(
            SUMMARY_DIR, 
            f"summary_duration_{USERS_PER_INTERVAL}users_{DURATION_MINUTES}m_{timestamp}.json"
        )
        summary_file_csv = os.path.join(
            SUMMARY_DIR, 
            f"summary_duration_{USERS_PER_INTERVAL}users_{DURATION_MINUTES}m_{timestamp}.csv"
        )

        # 寫 log
        with open(log_file, "w", encoding="utf-8") as f:
            for r in results:
                f.write(json.dumps(r, ensure_ascii=False) + "\n")

        # 寫 summary JSON
        summary = {
            "timestamp": timestamp,
            "interval": interval_count,
            "users": USERS_PER_INTERVAL,
            "pass": total_pass,
            "fail": total_fail,
            "avg_response_time": avg_time,
            "max_response_time": max_time,
            "stage_avg_times": stage_avg_times,
            "interval_start": (datetime.now() - timedelta(seconds=UNIT_INTERVAL_SEC)).strftime("%Y-%m-%d %H:%M:%S"),
            "interval_end": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        with open(summary_file_json, "w", encoding="utf-8") as f:
            json.dump(summary, f, ensure_ascii=False, indent=2)

        # 寫 summary CSV (單行)
        with open(summary_file_csv, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            header = ["timestamp","interval","users","pass","fail","avg_response_time","max_response_time"] + list(stage_avg_times.keys()) + ["interval_start","interval_end"]
            writer.writerow(header)
            writer.writerow([
                timestamp, interval_count, USERS_PER_INTERVAL, total_pass, total_fail,
                avg_time, max_time
            ] + list(stage_avg_times.values()) + [summary["interval_start"], summary["interval_end"]])

        # 分段顯示完成訊息
        print(f"Interval {interval_count} completed.")
        print(f"Log: {log_file},")
        print(f"Summary(JSON): {summary_file_json},")
        print(f"Summary(CSV): {summary_file_csv}\n")

if __name__ == "__main__":
    run_long_duration_test()
