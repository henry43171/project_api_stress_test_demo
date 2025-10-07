# utils/generate_report.py
import argparse
import json
import re
from pathlib import Path

import matplotlib.pyplot as plt


def generate_high_concurrency_report(summary_dir):

    summary_dir = Path(summary_dir)
    json_files = sorted(
        summary_dir.glob("*.json"),
        key=lambda f: int(re.search(r"_(\d+)u_", f.name).group(1))
    )

    all_data = []

    for f in json_files:
        with open(f, "r", encoding="utf-8") as file:
            data = json.load(file)
            all_data.append(data)

    print(f"[高併發報表] 已讀取 {len(all_data)} 筆 summary 檔案")

    # 準備 X、Y 資料
    batches = list(range(1, len(all_data) + 1))
    num_users = [d["NUM_USERS"] for d in all_data]
    success_rates = [d["success_rate"] * 100 for d in all_data]  # 百分比顯示


    # 列印 NUM_USERS 與 success_rate
    print("Batch | NUM_USERS | Success Rate (%)")
    print("-" * 30)
    for i, (n, s) in enumerate(zip(num_users, success_rates), 1):
        print(f"{i:5d} | {n:9d} | {s:14.2f}")


    fig, ax1 = plt.subplots(figsize=(8, 5))

    # 左 Y 軸：NUM_USERS
    ax1.plot(batches, num_users, color="tab:blue", marker="o", label="NUM_USERS")
    ax1.set_xlabel("Batch Index")
    ax1.set_ylabel("NUM_USERS", color="tab:blue")
    ax1.tick_params(axis="y", labelcolor="tab:blue")

    # 右 Y 軸：Success Rate
    ax2 = ax1.twinx()
    ax2.plot(batches, success_rates, color="tab:orange", marker="x", label="Success Rate")
    ax2.set_ylabel("Success Rate (%)", color="tab:orange")
    ax2.tick_params(axis="y", labelcolor="tab:orange")

    # 標題與圖例
    plt.title("High Concurrency Report")
    fig.tight_layout()
    ax1.legend(loc="upper left")
    ax2.legend(loc="upper right")

    plt.show()


def generate_long_duration_report(summary_dir):
    summary_dir = Path(summary_dir)
    json_files = sorted(summary_dir.glob("*.json"))
    all_data = []
    for f in json_files:
        with open(f, "r", encoding="utf-8") as file:
            data = json.load(file)
            all_data.append(data)
    # TODO: 根據 all_data 畫圖
    print(f"[長時間報表] 已讀取 {len(all_data)} 筆 summary 檔案")
    # plt.plot(range(len(all_data)), [d["users"] for d in all_data])
    # plt.title("Long Duration Users Per Interval")
    # plt.xlabel("Interval Index")
    # plt.ylabel("Users")
    # plt.show()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate test reports")
    parser.add_argument("--high_concurrency", action="store_true",
                        help="Generate high concurrency test report")
    parser.add_argument("--long_duration", action="store_true",
                        help="Generate long duration test report")
    args = parser.parse_args()

    if args.high_concurrency:
        generate_high_concurrency_report("results/summary/high_concurrency")
    elif args.long_duration:
        generate_long_duration_report("results/summary/long_duration")
    else:
        print("請指定 --high_concurrency 或 --long_duration")
