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

    fig, ax1 = plt.subplots(figsize=(10,6))

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
    fig.legend(loc="lower right", bbox_to_anchor=(1, 0), ncol=1)
    fig.tight_layout(rect=[0, 0, 0.9, 1])  # 留 15% 空間給右側圖例

    plt.show()


def generate_long_duration_report(summary_dir):
    summary_dir = Path(summary_dir)
    json_files = sorted(summary_dir.glob("*.json"))
    all_data = []

    for f in json_files:
        with open(f, "r", encoding="utf-8") as file:
            data = json.load(file)
            all_data.append(data)

    if not all_data:
        print("No JSON files found.")
        return

    # 只取第一個檔案的 period_stats
    period_stats = all_data[0]["period_stats"]

    periods = [p["period"] for p in period_stats]
    users = [p["users"] for p in period_stats]
    success_rates = [p["success_rate"] * 100 for p in period_stats]  # 百分比

    # 列印數值
    print("Period | Users | Success Rate (%)")
    print("-" * 30)
    for per, u, s in zip(periods, users, success_rates):
        print(f"{per:6d} | {u:5d} | {s:14.2f}")

    # 從這邊開始
    fig, ax1 = plt.subplots(figsize=(10,6))

    # Users 柱狀圖
    if max(users) > 0:
        bars = ax1.bar(periods, users, color=plt.cm.Blues([u/max(users) for u in users]), alpha=0.8)
    else:
        bars = ax1.bar(periods, users, color="tab:blue", alpha=0.8)

    ax1.set_xlabel("Period")
    ax1.set_ylabel("Users", color="tab:blue")
    ax1.tick_params(axis="y", labelcolor="tab:blue")

    # 在柱頂加數值
    for rect in ax1.patches:
        height = rect.get_height()
        ax1.text(rect.get_x() + rect.get_width()/2, height + 5, f"{height}", 
                ha='center', va='bottom', fontsize=8)

    # Success Rate 折線圖（優化風格）
    ax2 = ax1.twinx()
    # 折線
    ax2.plot(periods, success_rates, color="tab:orange", marker="o", markersize=5,
            linewidth=3, alpha=0.8, label="Success Rate")

    ax2.tick_params(axis="y", labelcolor="tab:orange")
    ax2.set_ylabel("Success Rate (%)", color="tab:orange")

    plt.title("Long Duration Report")
    # 調整圖表區域，避免圖例擋線
    fig.tight_layout(rect=[0, 0, 0.9, 1])
    # 圖例合併，放右下
    fig.legend(loc="lower right", bbox_to_anchor=(1.0, 0), ncol=1, fontsize=9)

    plt.show()


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
