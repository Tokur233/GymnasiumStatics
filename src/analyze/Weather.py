import pandas as pd
from pathlib import Path
import matplotlib.pyplot as plt
import seaborn as sns
import os

try:
    plt.rcParams["font.sans-serif"] = [
        "Microsoft YaHei",
        "SimHei",
        "WenQuanYi Micro Hei",
    ]
    plt.rcParams["axes.unicode_minus"] = False
except:
    pass


def analyze_weather_impact():
    current_file_dir = Path(__file__).resolve().parent
    project_root = current_file_dir.parent.parent
    data_dir = project_root / "data"
    analysis_dir = project_root / "analysis"
    analysis_dir.mkdir(parents=True, exist_ok=True)

    print(f"[INFO] Extracting final dataset with weather features...")
    all_files = list(data_dir.glob("gym_data_*.csv"))
    df = pd.concat(
        [pd.read_csv(f, low_memory=False) for f in all_files], ignore_index=True
    )

    df = df[df["site_id"] == 5].copy()
    df["time_range"] = df["time_range"].replace({
        "07:00-08:30": "06:30-08:00",
        "08:30-10:00": "08:00-09:30",
    })
    df["scrape_time"] = pd.to_datetime(df["scrape_time"])

    for col in ["booked", "temperature", "humidity", "aqi"]:
        df[col] = pd.to_numeric(df[col], errors="coerce")

    df_final = (
        df
        .sort_values("scrape_time")
        .groupby(["date", "time_range"])
        .last()
        .reset_index()
    )

    plt.figure(figsize=(8, 6))
    cols_to_corr = ["booked", "temperature", "humidity", "aqi"]

    df_corr = df_final[cols_to_corr].rename(
        columns={
            "booked": "Final Booked",
            "temperature": "Temperature (℃)",
            "humidity": "Humidity (%)",
            "aqi": "Air Quality (AQI)",
        }
    )

    corr_matrix = df_corr.corr(method="pearson")

    sns.heatmap(
        corr_matrix,
        annot=True,
        cmap="coolwarm",
        fmt=".2f",
        vmin=-1,
        vmax=1,
        linewidths=1,
        square=True,
        cbar_kws={"shrink": 0.8},
    )
    plt.title(
        "Pearson Correlation Matrix: Booking vs Weather Factors",
        fontsize=14,
        fontweight="bold",
        pad=15,
    )
    plt.tight_layout()
    plt.savefig(analysis_dir / "6_weather_correlation_matrix.png", dpi=300)
    print("[INFO] Weather correlation matrix saved to analysis directory")

    def categorize_weather(cond):
        if pd.isna(cond):
            return "Unknown"
        if any(w in cond for w in ["晴", "多云"]):
            return "Good (Sunny/Cloudy)"
        return "Bad (Rain/Snow/Overcast/Fog)"

    df_final["weather_type"] = df_final["condition"].apply(categorize_weather)
    df_plot = df_final[df_final["weather_type"] != "Unknown"]

    plt.figure(figsize=(10, 6))

    my_flierprops = dict(
        marker="o",
        markerfacecolor="white",
        markersize=6,
        markeredgecolor="black",
        alpha=0.8,
    )

    sns.boxplot(
        data=df_plot,
        x="weather_type",
        y="booked",
        palette="Set2",
        width=0.5,
        showfliers=True,
        flierprops=my_flierprops,
    )

    def mark_outliers(group):
        q1 = group.quantile(0.25)
        q3 = group.quantile(0.75)
        iqr = q3 - q1
        return (group < q1 - 1.5 * iqr) | (group > q3 + 1.5 * iqr)

    df_plot["is_outlier"] = df_plot.groupby("weather_type")["booked"].transform(
        mark_outliers
    )

    sns.stripplot(
        data=df_plot[~df_plot["is_outlier"]],
        x="weather_type",
        y="booked",
        color=".25",
        alpha=0.6,
        jitter=True,
        size=5,
    )

    plt.axhline(
        y=110, color="red", linestyle="--", alpha=0.5, label="Full Load Ceiling"
    )
    plt.title(
        "Weather Condition Impact on Gym Full Load", fontsize=14, fontweight="bold"
    )
    plt.xlabel("Weather Category", fontsize=12)
    plt.ylabel("Final Booked Count", fontsize=12)
    plt.legend()
    plt.grid(axis="y", linestyle="--", alpha=0.5)
    plt.tight_layout()
    plt.savefig(analysis_dir / "7_weather_impact_boxplot.png", dpi=300)
    print("[INFO] Weather impact boxplot saved to analysis directory")


if __name__ == "__main__":
    analyze_weather_impact()
