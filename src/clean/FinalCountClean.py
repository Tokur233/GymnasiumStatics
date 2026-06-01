import pandas as pd
import glob
import os


def clean_and_extract_fitness_data(target_venue=5):
    # 1. 动态定位项目根目录（兼容在根目录或 src/clean 目录下运行）
    current_dir = os.path.dirname(os.path.abspath(__file__))
    if "src" in current_dir:
        project_root = os.path.dirname(os.path.dirname(current_dir))
    else:
        project_root = current_dir

    data_pattern = os.path.join(project_root, "data", "gym_data_*.csv")
    print(f"📥 正在扫描数据文件: {data_pattern}")
    all_files = glob.glob(data_pattern)

    if not all_files:
        print("⚠️ 未找到任何数据文件，请检查 data/ 目录。")
        return

    # 2. 读取并合并所有天的 CSV
    df_list = [pd.read_csv(f, low_memory=False) for f in all_files]
    df = pd.concat(df_list, ignore_index=True)

    # 3. 过滤出健身房数据
    df_fit = df[df["site_id"] == target_venue].copy()
    if df_fit.empty:
        print(f"⚠️ 未找到 site_id={target_venue} 的健身房数据。")
        return

    print(f"✅ 成功加载健身房原始数据：{len(df_fit)} 条")

    # ==========================================
    # 核心逻辑 1：早期数据的对齐 (Data Harmonization)
    # ==========================================
    time_mapping = {
        "07:00-08:30": "06:30-08:00",
        "08:30-10:00": "08:00-09:30",
        # 10:00-11:30 未发生变化，无需映射
    }
    df_fit["time_range"] = df_fit["time_range"].replace(time_mapping)

    # 清洗数据类型
    df_fit["scrape_time"] = pd.to_datetime(df_fit["scrape_time"])
    df_fit["booked"] = (
        pd.to_numeric(df_fit["booked"], errors="coerce").fillna(0).astype(int)
    )

    # ==========================================
    # 核心逻辑 2：提取“最终锁定人数”
    # ==========================================
    # 排序：确保数据按抓取时间严格按照先后顺序排列
    df_fit = df_fit.sort_values(by="scrape_time")

    # 按照 date 和 time_range 分组，使用 .last() 获取该分组下最后一次抓取的记录
    # 根据业务逻辑，系统跑到 21:30 之后，当天的最后一条记录即为该场次的最终锁定状态
    df_final = df_fit.groupby(["date", "time_range"]).last().reset_index()

    # 仅保留你需要的精简字段：天数、时间段、最终人数
    df_final = df_final[["date", "time_range", "booked"]]
    df_final = df_final.rename(columns={"booked": "final_booked"})

    # 按照日期和时间段的自然顺序排序，方便阅读
    df_final = df_final.sort_values(by=["date", "time_range"]).reset_index(drop=True)

    # ==========================================
    # 4. 存储为轻量级的结构化文件
    # ==========================================
    output_dir = os.path.join(project_root, "analysis")
    os.makedirs(output_dir, exist_ok=True)
    output_file = os.path.join(output_dir, "fitness_daily_final.csv")

    df_final.to_csv(output_file, index=False, encoding="utf_8_sig")

    print("✅ 早期数据对齐成功！")
    print("✅ 最终锁定人数提取成功！")
    print(f"📊 每天各时段最终人数已精简保存至: {output_file}")
    print("\n--- 提取的数据预览 ---")
    print(df_final.head(10))


if __name__ == "__main__":
    clean_and_extract_fitness_data()
