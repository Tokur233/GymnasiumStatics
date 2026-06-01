import pandas as pd
from pathlib import Path


def clean_and_extract_fitness_data(target_venue=5):
    current_file_dir = Path(__file__).resolve().parent
    project_root = current_file_dir.parent.parent

    data_dir = project_root / "data"
    print(f"[INFO] Scanning data files: {data_dir / 'gym_data_*.csv'}")
    all_files = sorted(data_dir.glob("gym_data_*.csv"))

    if not all_files:
        print("[WARNING] No data files found. Please check the 'data/' directory.")
        return

    df_list = [pd.read_csv(f, low_memory=False) for f in all_files]
    df = pd.concat(df_list, ignore_index=True)

    df_fit = df[df["site_id"] == target_venue].copy()
    if df_fit.empty:
        print(f"[WARNING] No gym data found for site_id={target_venue}.")
        return

    print(f"[INFO] Loaded raw gym data: {len(df_fit)} records")

    time_mapping = {
        "07:00-08:30": "06:30-08:00",
        "08:30-10:00": "08:00-09:30",
    }
    df_fit["time_range"] = df_fit["time_range"].replace(time_mapping)

    df_fit["scrape_time"] = pd.to_datetime(df_fit["scrape_time"])
    df_fit["booked"] = (
        pd.to_numeric(df_fit["booked"], errors="coerce").fillna(0).astype(int)
    )

    df_fit = df_fit.sort_values(by="scrape_time")

    df_final = df_fit.groupby(["date", "time_range"]).last().reset_index()

    df_final = df_final[["date", "time_range", "booked"]]
    df_final = df_final.rename(columns={"booked": "final_booked"})

    df_final = df_final.sort_values(by=["date", "time_range"]).reset_index(drop=True)

    output_dir = project_root / "clean_data"
    output_dir.mkdir(parents=True, exist_ok=True)
    output_file = output_dir / "fitness_daily_final.csv"

    df_final.to_csv(str(output_file), index=False, encoding="utf_8_sig")

    print("[INFO] Early data alignment completed.")
    print("[INFO] Final booked counts extracted successfully.")
    print(f"[INFO] Daily final counts saved to: {output_file}")
    print("\n--- Extracted data preview ---")
    print(df_final.head(10))


if __name__ == "__main__":
    clean_and_extract_fitness_data()
