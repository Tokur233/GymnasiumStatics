import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path

current_file_dir = Path(__file__).resolve().parent
project_root = current_file_dir.parent.parent

try:
    plt.rcParams["font.sans-serif"] = [
        "Microsoft YaHei",
        "SimHei",
        "WenQuanYi Micro Hei",
    ]
    plt.rcParams["axes.unicode_minus"] = False
except:
    pass


def plot_final_fitness_data():
    file_path = project_root / "clean_data" / "fitness_daily_final.csv"

    if not file_path.exists():
        print(
            f"[WARNING] File not found: {file_path}. Please run the data cleaning script first."
        )
        return

    print("[INFO] Reading final dataset...")
    df = pd.read_csv(file_path)

    df["start_time"] = df["time_range"].str.split("-").str[0]
    df["exact_datetime"] = pd.to_datetime(df["date"] + " " + df["start_time"])

    week_map = {
        0: "Mon",
        1: "Feb",
        2: "Wed",
        3: "Thu",
        4: "Fri",
        5: "Sat",
        6: "Sun",
    }
    df["weekday_num"] = pd.to_datetime(df["date"]).dt.dayofweek
    df["weekday"] = df["weekday_num"].map(week_map)

    df = df.sort_values(by="exact_datetime").reset_index(drop=True)

    # IQR
    def get_normal_data(dataframe, group_col):
        """根据传入的分组列，过滤掉异常值，返回仅包含正常波动数据的 DataFrame"""

        def mark_outliers(group):
            q1 = group.quantile(0.25)
            q3 = group.quantile(0.75)
            iqr = q3 - q1
            lower_bound = q1 - 1.5 * iqr
            upper_bound = q3 + 1.5 * iqr
            return (group < lower_bound) | (group > upper_bound)

        is_outlier = dataframe.groupby(group_col)["final_booked"].transform(
            mark_outliers
        )
        return dataframe[~is_outlier]

    df_normal_time = get_normal_data(df, "time_range")
    df_normal_week = get_normal_data(df, "weekday")

    output_dir = project_root / "analysis"
    output_dir.mkdir(parents=True, exist_ok=True)

    # Heatmap
    plt.figure(figsize=(16, 8))

    df["short_date"] = pd.to_datetime(df["date"]).dt.strftime("%m-%d")
    heatmap_data = df.pivot(
        index="time_range", columns="short_date", values="final_booked"
    )

    sns.heatmap(
        heatmap_data,
        cmap="YlOrRd",
        annot=True,
        fmt=".0f",
        vmin=0,
        vmax=110,
        linewidths=0.5,
        cbar_kws={"label": "Final Bookings (0-110)"},
    )

    plt.title("Gym Reservation Heatmap", fontsize=16, fontweight="bold")
    plt.xlabel("Date", fontsize=12)
    plt.ylabel("Time Slot", fontsize=12)

    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.savefig(str(output_dir / "3_heatmap_distribution.png"), dpi=300)
    print("[INFO] 1. Time heatmap saved (replaced the original scatterplot)")

    my_flierprops = dict(
        marker="o",
        markerfacecolor="white",
        markersize=6,
        markeredgecolor="black",
        alpha=0.8,
    )

    # Time_Range Boxplot
    plt.figure(figsize=(14, 7))
    time_order = sorted(df["time_range"].unique())

    sns.boxplot(
        data=df,
        x="time_range",
        y="final_booked",
        hue="time_range",
        order=time_order,
        palette="Set3",
        legend=False,
        width=0.6,
        showfliers=True,
        flierprops=my_flierprops,
    )

    sns.stripplot(
        data=df_normal_time,
        x="time_range",
        y="final_booked",
        order=time_order,
        color=".25",
        alpha=0.6,
        jitter=True,
        size=4,
    )

    plt.axhline(y=110, color="red", linestyle="--", linewidth=1.5)
    plt.title(
        "Time Range Boxplot",
        fontsize=16,
        fontweight="bold",
    )
    plt.xlabel("Time Range", fontsize=12)
    plt.ylabel("Final Bookings", fontsize=12)
    plt.xticks(rotation=45)
    plt.grid(axis="y", linestyle="--", alpha=0.5)
    plt.tight_layout()
    plt.savefig(str(output_dir / "4_boxplot_by_timerange.png"), dpi=300)
    print("[INFO] 2. Boxplot by time slot saved")

    # Day of the week Boxplot
    plt.figure(figsize=(10, 6))
    week_order = ["Mon", "Feb", "Wed", "Thu", "Fri", "Sat", "Sun"]

    sns.boxplot(
        data=df,
        x="weekday",
        y="final_booked",
        hue="weekday",
        order=week_order,
        palette="Pastel1",
        legend=False,
        width=0.6,
        showfliers=True,
        flierprops=my_flierprops,
    )

    sns.stripplot(
        data=df_normal_week,
        x="weekday",
        y="final_booked",
        order=week_order,
        color=".25",
        alpha=0.6,
        jitter=True,
        size=4,
    )

    plt.axhline(y=110, color="red", linestyle="--", linewidth=1.5)
    plt.title(
        "Day-of-Week Boxplot",
        fontsize=16,
        fontweight="bold",
    )
    plt.xlabel("Day of the Week", fontsize=12)
    plt.ylabel("Final Bookings", fontsize=12)
    plt.grid(axis="y", linestyle="--", alpha=0.5)
    plt.tight_layout()
    plt.savefig(str(output_dir / "5_boxplot_by_weekday.png"), dpi=300)
    print("[INFO] 3. Boxplot by weekday saved")


if __name__ == "__main__":
    plot_final_fitness_data()
