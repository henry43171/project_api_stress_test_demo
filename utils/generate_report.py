# utils/generate_report.py
import argparse
import json
import re
from pathlib import Path

import matplotlib.pyplot as plt


# -----------------------------
# 柱狀圖函式
# -----------------------------
def plot_bar(ax, x, y, label="Users", color="tab:blue", alpha=0.8, show_value=True, value_offset=5):
    """在指定的 ax 畫柱狀圖"""
    if max(y) > 0:
        # 使用漸層顏色
        bars = ax.bar(x, y, color=plt.cm.Blues([v/max(y) for v in y]), alpha=alpha)
    else:
        bars = ax.bar(x, y, color=color, alpha=alpha)

    ax.set_ylabel(label, color=color)
    ax.tick_params(axis="y", labelcolor=color)

    # 在柱頂加數值
    if show_value:
        for rect in ax.patches:
            height = rect.get_height()
            ax.text(rect.get_x() + rect.get_width()/2, height + value_offset, f"{height}",
                    ha='center', va='bottom', fontsize=8)

    return bars

# -----------------------------
# 折線圖函式
# -----------------------------
def plot_line(ax, x, y, label="Success Rate", color="tab:orange", marker="o", linewidth=3, alpha=0.8):
    """在指定的 ax 畫折線圖"""
    line, = ax.plot(x, y, color=color, marker=marker, markersize=5, linewidth=linewidth, alpha=alpha, label=label)
    ax.set_ylabel(f"{label} (%)", color=color)
    ax.tick_params(axis="y", labelcolor=color)
    return line


# -----------------------------
# 高併發報表
# -----------------------------
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

    # 準備資料
    batches = list(range(1, len(all_data) + 1))
    num_users = [d["NUM_USERS"] for d in all_data]
    success_rates = [d["success_rate"] * 100 for d in all_data]  # 百分比

    # 列印數值
    # print("Batch | NUM_USERS | Success Rate (%)")
    # print("-" * 30)
    # for i, (n, s) in enumerate(zip(num_users, success_rates), 1):
    #     print(f"{i:5d} | {n:9d} | {s:14.2f}")

    # -----------------------------
    # 畫圖
    fig, ax1 = plt.subplots(figsize=(10,6))

    # NUM_USERS 用柱狀圖
    bars = plot_bar(ax1, batches, num_users, label="NUM_USERS", color="tab:blue")

    # Success Rate 用折線圖
    ax2 = ax1.twinx()
    line = plot_line(ax2, batches, success_rates, label="Success Rate", color="tab:orange")

    ax1.set_xlabel("Batch Index")
    plt.title("High Concurrency Report")

    # 調整圖表區域與圖例
    fig.tight_layout(rect=[0, 0, 0.9, 1])
    fig.legend(loc="lower right", bbox_to_anchor=(1.0, 0), ncol=1, fontsize=9)

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

    # # 列印數值
    # print("Period | Users | Success Rate (%)")
    # print("-" * 30)
    # for per, u, s in zip(periods, users, success_rates):
    #     print(f"{per:6d} | {u:5d} | {s:14.2f}")

    # -----------------------------
    # 從這邊開始畫圖
    fig, ax1 = plt.subplots(figsize=(10,6))

    # 畫柱狀圖
    bars = plot_bar(ax1, periods, users, label="Users", color="tab:blue", alpha=0.8)

    # 畫折線圖
    ax2 = ax1.twinx()
    line = plot_line(ax2, periods, success_rates, label="Success Rate", color="tab:orange")

    ax1.set_xlabel("Period")
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
