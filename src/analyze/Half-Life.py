import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path

try:
    plt.rcParams["font.sans-serif"] = [
        "Microsoft YaHei",
        "SimHei",
        "WenQuanYi Micro Hei",
    ]
    plt.rcParams["axes.unicode_minus"] = False
except:
    pass


def analyze_and_plot_lifecycle():
    current_file_dir = Path(__file__).resolve().parent
    project_root = current_file_dir.parent.parent
    data_dir = project_root / "data"
    output_dir = project_root / "analysis"
    output_dir.mkdir(parents=True, exist_ok=True)

    print(f"[INFO] Scanning raw dynamic data: {data_dir}")
    all_files = list(data_dir.glob("gym_data_*.csv"))
    if not all_files:
        print("[WARNING] No data files found.")
        return

    df = pd.concat(
        [pd.read_csv(f, low_memory=False) for f in all_files], ignore_index=True
    )

    df = df[df["site_id"] == 5].copy()
    df["time_range"] = df["time_range"].replace({
        "07:00-08:30": "06:30-08:00",
        "08:30-10:00": "08:00-09:30",
    })

    df["scrape_time"] = pd.to_datetime(df["scrape_time"])
    df["booked"] = pd.to_numeric(df["booked"], errors="coerce").fillna(0).astype(int)

    df["release_time"] = (
        pd.to_datetime(df["date"]) - pd.Timedelta(days=1) + pd.Timedelta(hours=8)
    )

    df["hours_elapsed"] = (
        df["scrape_time"] - df["release_time"]
    ).dt.total_seconds() / 3600

    print("[INFO] Calculating half-life and full-load points for each session...")
    results = []

    for (date, time_range), group in df.groupby(["date", "time_range"]):
        group = group.sort_values(by="hours_elapsed", ascending=True)

        hit_50 = group[group["booked"] >= 55]
        half_life_hours = hit_50.iloc[0]["hours_elapsed"] if not hit_50.empty else None

        hit_100 = group[group["booked"] >= 110]
        full_load_hours = (
            hit_100.iloc[0]["hours_elapsed"] if not hit_100.empty else None
        )

        results.append({
            "date": date,
            "time_range": time_range,
            "half_life_hours": half_life_hours,
            "full_load_hours": full_load_hours,
        })

    df_results = pd.DataFrame(results)

    summary = (
        df_results
        .groupby("time_range")
        .agg(
            half_life_hours=("half_life_hours", "mean"),
            full_load_hours=("full_load_hours", "mean"),
            total_days=("date", "count"),
            half_load_days=("half_life_hours", "count"),
            full_load_days=("full_load_hours", "count"),
        )
        .reset_index()
    )

    summary["second_half_duration"] = (
        summary["full_load_hours"] - summary["half_life_hours"]
    )

    summary["half_load_rate"] = (
        summary["half_load_days"] / summary["total_days"]
    ) * 100

    summary["full_load_rate"] = (
        summary["full_load_days"] / summary["total_days"]
    ) * 100

    summary = summary.sort_values(by="time_range", ascending=False).round(2)

    slots = summary["time_range"].tolist()
    half_life = summary["half_life_hours"].tolist()
    remainder = summary["second_half_duration"].tolist()
    rates = summary["full_load_rate"].tolist()
    half_rates = summary["half_load_rate"].round(1).tolist()

    print("\n[INFO] Calculation complete. Previewing summary:")

    print_cols = [
        "time_range",
        "half_life_hours",
        "half_load_rate",
        "full_load_hours",
        "second_half_duration",
        "full_load_rate",
    ]
    print(summary[print_cols].to_string(index=False))

    print("\n[INFO] Rendering lifecycle stacked bar chart...")
    fig, ax = plt.subplots(figsize=(12, 7))

    bars1 = ax.barh(
        slots,
        half_life,
        color="#B22222",
        alpha=0.85,
        label="First half duration (0 → 50%)",
        height=0.6,
        edgecolor="white",
    )

    bars2 = ax.barh(
        slots,
        remainder,
        left=half_life,
        color="#FFA07A",
        alpha=0.8,
        label="Second half duration (50% → 100%)",
        height=0.6,
        edgecolor="white",
    )

    for i, (h, r, rate, h_rate) in enumerate(
        zip(half_life, remainder, rates, half_rates)
    ):
        if not np.isnan(h):
            y_pos_h = i + 0.35 if h < 3 else i
            font_color_h = "black" if h < 3 else "white"
            text_str_h = f"{h}h ({h_rate}%)" if h < 3 else f"{h}h\n({h_rate}%)"

            ax.text(
                h / 2 + 1.2,
                y_pos_h,
                text_str_h,
                va="center",
                ha="center",
                color=font_color_h,
                fontweight="bold",
                fontsize=9,
            )

        if not np.isnan(r):
            y_pos_r = i + 0.35 if r < 3 else i
            text_str_r = f"{r}h ({rate}%)" if r < 3 else f"{r}h\n({rate}%)"

            ax.text(
                h + r / 2,
                y_pos_r,
                text_str_r,
                va="center",
                ha="center",
                color="black",
                fontweight="bold",
                fontsize=9,
            )

            ax.text(
                h + r + 1,
                i,
                f"Full load ({round(h + r, 1)}h)",
                va="center",
                ha="left",
                color="#666666",
                fontsize=10,
                style="italic",
            )
        else:
            offset_x = h + 1 if not np.isnan(h) else 1
            ax.text(
                offset_x,
                i,
                f"Not full loaded | Rate: {rate}%",
                va="center",
                ha="left",
                color="#8B0000",
                fontsize=10,
                style="italic",
                fontweight="bold",
            )

    ax.set_title(
        "Gym reservation lifecycle by time slot",
        fontsize=16,
        fontweight="bold",
        pad=20,
    )
    ax.set_xlabel(
        "Hours elapsed since ticket release at 08:00 the previous day",
        fontsize=12,
        labelpad=10,
    )
    ax.set_ylabel("Time Slot", fontsize=12)

    ax.set_xlim(0, 48)

    ax.xaxis.grid(True, linestyle="--", alpha=0.4)
    ax.yaxis.grid(False)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)

    ax.legend(
        loc="upper center",
        bbox_to_anchor=(0.5, -0.15),
        ncol=2,
        frameon=True,
        fontsize=11,
    )

    plt.tight_layout()

    svg_path = output_dir / "8_lifecycle_stacked_bar.svg"
    png_path = output_dir / "8_lifecycle_stacked_bar.png"
    plt.savefig(svg_path, format="svg")
    plt.savefig(png_path, dpi=300)

    print(
        f"[INFO] Lifecycle charts generated.\nSVG path: {svg_path}\nPNG path: {png_path}"
    )


if __name__ == "__main__":
    analyze_and_plot_lifecycle()
