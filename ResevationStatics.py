import hashlib
import os
import time
from datetime import datetime, timedelta, timezone
from typing import Optional, Any, Dict
import json
import pandas as pd
import requests
import urllib3
from dotenv import load_dotenv


urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


load_dotenv()
config_str = os.environ.get("CONFIG", "{}")
try:
    config_data = json.loads(config_str)
except json.JSONDecodeError:
    config_data = {}

CG_AUTH = config_data.get("CG_AUTH") or os.environ.get("CG_AUTH", "")
COOKIE = config_data.get("CG_COOKIE") or os.environ.get("CG_COOKIE", "")
SALT = config_data.get("SALT") or os.environ.get("SALT", "")
APP_KEY = config_data.get("APP_KEY") or os.environ.get("APP_KEY", "")

BASE_URL = config_data.get("BASE_URL") or os.environ.get("BASE_URL", "")
API_PATH = config_data.get("API_PATH") or os.environ.get("API_PATH", "")


VENUE_IDS = [5]


STATUS_MAP = {1: "可预约", 2: "不开放/已过期", 3: "未支付锁定", 4: "已售/已满"}


def generate_sign(path: str, params: Dict[str, Any], timestamp: str) -> str:

    sign_str = SALT + path
    if params:
        for key in sorted(params.keys()):
            val = params[key]
            if val is not None and str(val) != "" and not isinstance(val, (dict, list)):
                sign_str += str(key) + str(val)
    sign_str += str(timestamp) + " " + SALT
    return hashlib.md5(sign_str.encode("utf-8")).hexdigest()


def get_data(site_id: int, date_str: str) -> Optional[Dict[str, Any]]:

    ts = str(int(time.time() * 1000))
    params = {
        "venueSiteId": str(site_id),
        "searchDate": date_str,
        "hasReserveInfo": "1",
        "nocache": ts,
    }

    headers = {
        "Accept": "application/json, text/plain, */*",
        "app-key": APP_KEY,
        "timestamp": ts,
        "sign": generate_sign(API_PATH, params, ts),
        "cgAuthorization": CG_AUTH,
        "Cookie": COOKIE,
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Referer": f"https://cgyy.qd.sdu.edu.cn/venue/venue-reservation/{site_id}",
    }

    try:
        resp = requests.get(
            BASE_URL + API_PATH,
            params=params,
            headers=headers,
            timeout=15,
            verify=False,
        )
        if resp.status_code == 200:
            return resp.json()
    except requests.exceptions.RequestException as e:
        print(f"Request Error on Site {site_id}: {e}")
    return None


def main() -> None:
    tz_utc_8 = timezone(timedelta(hours=8))
    now_utc8 = datetime.now(tz_utc_8)

    today = now_utc8.strftime("%Y-%m-%d")
    tomorrow = (now_utc8 + timedelta(days=1)).strftime("%Y-%m-%d")

    results = []
    scrape_time = now_utc8.strftime("%Y-%m-%d %H:%M:%S")

    for vid in VENUE_IDS:
        for date in [today, tomorrow]:
            print(f"Scraping Site {vid} on {date}...", end=" ")
            json_data = get_data(vid, date)

            if json_data and json_data.get("code") == 200 and "data" in json_data:
                data_obj = json_data.get("data")
                if not data_obj:
                    print("Skipped (Data is null)")
                    continue

                total_capacity = data_obj.get("reservationTotalNum", 1)

                site_param = data_obj.get("siteParam") or {}
                parent_venue_name = site_param.get("siteName", f"Site_{vid}")

                date_space_info = data_obj.get("reservationDateSpaceInfo") or {}
                space_list = date_space_info.get(date, [])

                if not space_list:
                    print("Failed (No slots available)")
                    continue

                for space in space_list:
                    sub_space_name = space.get("spaceName", "")
                    if not sub_space_name or sub_space_name == parent_venue_name:
                        full_venue_name = parent_venue_name
                    else:
                        full_venue_name = f"{parent_venue_name}-{sub_space_name}"

                    for _, slot_data in space.items():
                        if (
                            isinstance(slot_data, dict)
                            and "reservationStatus" in slot_data
                        ):
                            start_time = slot_data.get("startDate", "").split(" ")[-1]
                            end_time = slot_data.get("endDate", "").split(" ")[-1]

                            booked_num = slot_data.get("alreadyNum")
                            if booked_num is None:
                                booked_num = slot_data.get("useNum", 0)

                            remark_parts = []
                            if slot_data.get("adminTake") is True and slot_data.get(
                                "adminRemark"
                            ):
                                remark_parts.append(slot_data.get("adminRemark"))

                            if slot_data.get("takeUp") is True and slot_data.get(
                                "takeUpExplain"
                            ):
                                remark_parts.append(slot_data.get("takeUpExplain"))

                            remark = " | ".join(remark_parts)

                            status_code = slot_data.get("reservationStatus")
                            status_key = (
                                int(status_code) if status_code is not None else -1
                            )
                            status_text = STATUS_MAP.get(
                                status_key, f"未知({status_code})"
                            )

                            results.append({
                                "scrape_time": scrape_time,
                                "date": date,
                                "site_id": vid,
                                "venue_name": full_venue_name,
                                "time_range": f"{start_time}-{end_time}",
                                "booked": booked_num,
                                "total": total_capacity,
                                "status": status_text,
                                "remark": remark,
                            })
                print("Parsed Successfully")
            else:
                msg = json_data.get("message") if json_data else "No Response"
                print(f"Skipped: {msg}")

            time.sleep(1.2)

    if results:
        df_new = pd.DataFrame(results)
        file_path = "gym_data.csv"

        if os.path.exists(file_path):
            try:
                df_old = pd.read_csv(file_path)
                df_combined = pd.concat([df_old, df_new], ignore_index=True)
            except pd.errors.ParserError:
                backup_path = file_path.replace(
                    ".csv", f"_backup_{int(time.time())}.csv"
                )
                os.rename(file_path, backup_path)
                print(
                    f"\n[WARNING] 发现旧版数据格式冲突，已将原文件备份为: {backup_path}"
                )
                df_combined = df_new
        else:
            df_combined = df_new

        df_combined["sort_time"] = (
            df_combined["time_range"]
            .astype(str)
            .apply(lambda x: x.split("-")[0] if "-" in x else x)
        )

        df_combined = df_combined.sort_values(
            by=["date", "site_id", "venue_name", "sort_time", "scrape_time"],
            ascending=[True, True, True, True, True],
        )

        df_combined = df_combined.drop(columns=["sort_time"])

        df_combined.to_csv(file_path, mode="w", index=False, encoding="utf_8_sig")
        print(
            f"\n[DONE] Global sorted and saved total {len(df_combined)} records to {file_path}."
        )
    else:
        print("\n[ERROR] No records parsed.")


if __name__ == "__main__":
    main()
