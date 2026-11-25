from pathlib import Path
import pandas as pd


def build_electricity_weather_dataset(
    raw_dir: Path,
    processed_dir: Path,
    city: str = "Madrid",
    convert_kelvin_to_celsius: bool = True,
) -> pd.DataFrame:
    energy_path = raw_dir / "energy_dataset.csv"
    weather_path = raw_dir / "weather_features.csv"

    if not energy_path.exists() or not weather_path.exists():
        raise FileNotFoundError(
            f"Không tìm thấy dữ liệu gốc tại {raw_dir}. "
            "Hãy đảm bảo 'energy_dataset.csv' và 'weather_features.csv' đã nằm trong datasets/raw/."
        )

    # 1. Đọc và làm sạch dữ liệu phụ tải điện (Energy)
    df_energy = pd.read_csv(energy_path, usecols=["time", "total load actual"])
    df_energy = df_energy.rename(columns={"total load actual": "load"})
    df_energy["time"] = pd.to_datetime(df_energy["time"], utc=True)
    df_energy = df_energy.sort_values("time")
    # Preserve missing target observations.  Filling ``load`` here would use
    # future target values (and would therefore leak information into
    # validation/test).  The notebook applies a causal, past-only treatment
    # for model inputs and keeps an observed-target mask for evaluation.

    # 2. Đọc và làm sạch dữ liệu thời tiết (Weather)
    df_weather = pd.read_csv(
        weather_path, usecols=["dt_iso", "city_name", "temp", "humidity", "wind_speed"]
    )
    df_weather["city_name"] = df_weather["city_name"].str.strip()

    if city.lower() == "all":
        df_weather_filtered = df_weather.copy()
    else:
        df_weather_filtered = df_weather[df_weather["city_name"] == city].copy()
        if df_weather_filtered.empty:
            raise ValueError(
                f"Thành phố '{city}' không tồn tại trong weather_features.csv."
            )

    df_weather_filtered["time"] = pd.to_datetime(df_weather_filtered["dt_iso"], utc=True)

    # Khử trùng lặp timestamp bằng trung bình cộng theo từng giờ
    df_weather_clean = (
        df_weather_filtered.groupby("time", as_index=False)[
            ["temp", "humidity", "wind_speed"]
        ]
        .mean()
        .rename(columns={"temp": "temperature"})
    )

    if convert_kelvin_to_celsius:
        df_weather_clean["temperature"] = df_weather_clean["temperature"] - 273.15

    # 3. Ghép bảng theo mốc thời gian UTC và cố định tần suất 1h
    df_merged = pd.merge(df_energy, df_weather_clean, on="time", how="inner")
    df_merged = (
        df_merged.set_index("time")
        .sort_index()
        .asfreq("1h")
    )

    # Weather is an input signal.  If a timestamp gap is introduced by the
    # hourly reindex, use only the last observed value; never use future
    # weather or interpolate the target ``load`` in the canonical dataset.
    weather_cols = ["temperature", "humidity", "wind_speed"]
    df_merged[weather_cols] = df_merged[weather_cols].ffill()

    # 4. Lưu kết quả ra thư mục processed/
    processed_dir.mkdir(parents=True, exist_ok=True)
    output_path = processed_dir / "electricity_load_weather_hourly.csv"
    df_merged.to_csv(output_path)

    return df_merged


def main() -> None:
    practice_dir = Path(__file__).resolve().parents[1]
    raw_dir = practice_dir / "datasets" / "raw"
    processed_dir = practice_dir / "datasets" / "processed"

    df = build_electricity_weather_dataset(
        raw_dir=raw_dir,
        processed_dir=processed_dir,
        city="Madrid",
        convert_kelvin_to_celsius=True,
    )

    print(f"Đã tạo thành công dataset tại: {processed_dir / 'electricity_load_weather_hourly.csv'}")
    print(f"Kích thước dữ liệu (rows, cols): {df.shape}")
    print(f"Số lượng giá trị NaN còn lại: {df.isna().sum().to_dict()}")
    print("\n5 dòng đầu tiên:")
    print(df.head())


if __name__ == "__main__":
    main()
