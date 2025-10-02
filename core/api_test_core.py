# core/simple_api_test_core.py
import json
import time
import requests
from pathlib import Path

# 讀取 config
CONFIG_PATH = Path("config/core.json")
with open(CONFIG_PATH, "r", encoding="utf-8") as f:
    config = json.load(f)

BASE_URL = config.get("BASE_URL", "http://127.0.0.1:5000")

# 假資料路徑
FAKE_DATA_PATH = Path("fake_data/fake_form_data.json")
with open(FAKE_DATA_PATH, "r", encoding="utf-8") as f:
    fake_data_list = json.load(f)


def log_result(index, step, success, elapsed, extra_msg=""):
    status = "V" if success else "X"
    print(f"[{status}] #{index+1} | {step} | {elapsed:.3f}s {extra_msg}")

# ----------------------
# 三個核心函式
# ----------------------
def visit_landing_page():
    t0 = time.time()
    r = requests.get(f"{BASE_URL}/landing_page")
    elapsed = time.time() - t0
    return r, elapsed


def start_form():
    t0 = time.time()
    r = requests.post(f"{BASE_URL}/start_form")
    elapsed = time.time() - t0
    return r, elapsed


def submit_form(data):
    t0 = time.time()
    r = requests.post(f"{BASE_URL}/submit_form", json=data)
    elapsed = time.time() - t0
    return r, elapsed


# ----------------------
# 核心測試流程
# ----------------------
def core_test(data, index=0):
    start_time = time.time()
    try:
        # 1. 進入首頁
        r1, elapsed = visit_landing_page()
        log_result(index, "GET /landing_page", r1.status_code == 200, elapsed)

        # 2. 點擊填表按鈕，拿到空表單
        r2, elapsed = start_form()
        log_result(index, "POST /start_form", r2.status_code == 200, elapsed)

        # 3. 送出表單
        r3, elapsed = submit_form(data)
        log_result(index, "POST /submit_form", r3.status_code == 200, elapsed)

        total_elapsed = time.time() - start_time
        print(f"#{index+1} Full workflow completed, total time {total_elapsed:.3f}s\n")

    except Exception as e:
        print(f"#{index+1} 測試出錯: {e}")


if __name__ == "__main__":
    core_test(fake_data_list[0], index=0)