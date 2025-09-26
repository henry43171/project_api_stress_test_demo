import argparse
import json
import matplotlib.pyplot as plt
from pathlib import Path

def generate_high_concurrency_report(summary_dir):
    summary_dir = Path(summary_dir)
    json_files = sorted(summary_dir.glob("summary_concurrent_*.json"))
    all_data = []
    for f in json_files:
        with open(f, "r", encoding="utf-8") as file:
            data = json.load(file)
            all_data.append(data)
    # TODO: 根據 all_data 畫圖
    print(f"[高併發報表] 已讀取 {len(all_data)} 筆 summary 檔案")
    # 範例簡單畫圖
    plt.plot(range(len(all_data)), [d["avg_response_time"] for d in all_data])
    plt.title("High Concurrency Avg Response Time")
    plt.xlabel("Batch Index")
    plt.ylabel("Avg Response Time (s)")
    plt.show()

def generate_long_duration_report(summary_dir):
    summary_dir = Path(summary_dir)
    json_files = sorted(summary_dir.glob("summary_duration_*.json"))
    all_data = []
    for f in json_files:
        with open(f, "r", encoding="utf-8") as file:
            data = json.load(file)
            all_data.append(data)
    # TODO: 根據 all_data 畫圖
    print(f"[長時間報表] 已讀取 {len(all_data)} 筆 summary 檔案")
    plt.plot(range(len(all_data)), [d["users"] for d in all_data])
    plt.title("Long Duration Users Per Interval")
    plt.xlabel("Interval Index")
    plt.ylabel("Users")
    plt.show()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate test reports")
    parser.add_argument("--high_concurrency", action="store_true",
                        help="Generate high concurrency test report")
    parser.add_argument("--long_duration", action="store_true",
                        help="Generate long duration test report")
    args = parser.parse_args()

    if args.high_concurrency:
        generate_high_concurrency_report("summary/high_concurrency")
    elif args.long_duration:
        generate_long_duration_report("summary/long_duration")
    else:
        print("請指定 --high_concurrency 或 --long_duration")
