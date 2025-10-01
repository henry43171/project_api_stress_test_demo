import os
import time
import json
from concurrent.futures import ThreadPoolExecutor, as_completed
from core.api_test_core import simulate_user, fake_forms, BATCH_SIZE, BATCH_DELAY
from datetime import datetime
import csv

# 讀取高併發測試參數
with open("config/high_concurrency.json", "r", encoding="utf-8") as f:
    config = json.load(f)

CONCURRENT_USERS_LIST = config["CONCURRENT_USERS_LIST"]
MAX_WORKERS = config["MAX_WORKERS"]
BATCH_PAUSE = config["BATCH_PAUSE"]

# 檔案/資料夾結構
LOG_DIR = "results/logs/high_concurrency"
SUMMARY_DIR = "results/summary/high_concurrency"
os.makedirs(LOG_DIR, exist_ok=True)
os.makedirs(SUMMARY_DIR, exist_ok=True)

def run_high_concurrency_test(num_users):
    start_total = time.time()
    results = []

    forms_to_use = fake_forms[:num_users]

    # 分批次
    for i in range(0, num_users, BATCH_SIZE):
        batch_forms = forms_to_use[i:i+BATCH_SIZE]
        max_workers = min(len(batch_forms), MAX_WORKERS)
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = [executor.submit(simulate_user, i+j+1, batch_forms[j]) for j in range(len(batch_forms))]
            for future in as_completed(futures):
                results.append(future.result())
        time.sleep(BATCH_DELAY)

    end_total = time.time()

    # 統計
    total_pass = sum(1 for r in results if r["success"] == "PASS")
    total_fail = num_users - total_pass
    avg_time = sum(r["elapsed"] for r in results) / len(results)
    max_time = max(r["elapsed"] for r in results)

    stage_times = {"visit_home": [], "start_form": [], "submit_form": [], "refresh_page": []}
    for r in results:
        for act in r["actions"]:
            stage_times[act].append(r["elapsed"])

    stage_avg_times = {stage: (sum(times)/len(times) if times else None) for stage, times in stage_times.items()}

    # 檔名時間
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_file = os.path.join(LOG_DIR, f"hc_{num_users}_{timestamp}.log")
    summary_file_json = os.path.join(SUMMARY_DIR, f"summary_concurrent_{num_users}_{timestamp}.json")
    summary_file_csv = os.path.join(SUMMARY_DIR, f"summary_concurrent_{num_users}_{timestamp}.csv")

    # 寫 log
    with open(log_file, "w", encoding="utf-8") as f:
        for r in results:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")

    # 寫 summary JSON
    summary = {
        "timestamp": timestamp,
        "num_users": num_users,
        "pass": total_pass,
        "fail": total_fail,
        "avg_response_time": avg_time,
        "max_response_time": max_time,
        "total_test_duration": end_total - start_total,
        "stage_avg_times": stage_avg_times
    }
    with open(summary_file_json, "w", encoding="utf-8") as f:
        json.dump(summary, f, ensure_ascii=False, indent=2)

    # 寫 summary CSV (單行)
    with open(summary_file_csv, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        header = ["timestamp","num_users","pass","fail","avg_response_time","max_response_time","total_test_duration"] + list(stage_avg_times.keys())
        writer.writerow(header)
        writer.writerow([
            timestamp, num_users, total_pass, total_fail, avg_time, max_time, end_total - start_total
        ] + list(stage_avg_times.values()))

    print(f"High concurrency test for {num_users} users completed.")
    print(f"Log: {log_file}")
    print(f"Summary(json): {summary_file_json}")
    print(f"Summary(csv): {summary_file_csv}")

if __name__ == "__main__":
    total_batches = len(CONCURRENT_USERS_LIST)
    for idx, users in enumerate(CONCURRENT_USERS_LIST, start=1):
        print(f"({idx}/{total_batches}) Running high concurrency test for {users} users...")
        run_high_concurrency_test(users)
        if idx < total_batches:
            print(f"Waiting {BATCH_PAUSE} seconds before next batch...\n")
            time.sleep(BATCH_PAUSE)
