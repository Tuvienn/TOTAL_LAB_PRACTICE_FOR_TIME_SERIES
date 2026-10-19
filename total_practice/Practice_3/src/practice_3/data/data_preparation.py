from pathlib import Path
import hashlib
import json

import pandas as pd

EXPECTED_RAW_SHA256 = (
    "109d122f7b485555c609eecdec2cd5a03172e0a08acd358d863acc93eb452585"
)

DATETIME_FORMAT = "%Y-%m-%d %H:%M:%S"

EXPECTED_RAW_ROWS = 121_273
EXPECTED_PREPARED_ROWS = 121_296
EXPECTED_MISSING_TIMESTAMPS = 27
EXPECTED_DUPLICATE_TIMESTAMPS = 4

# 1. File intefrity
def calculate_sha256(path: Path) -> str:

    sha256 = hashlib.sha256()

    with path.open("rb") as file:
        for chunk in iter(lambda: file.read(8192), b""):
            sha256.update(chunk)

    return sha256.hexdigest()

def validate_raw_file(path: Path) -> str:

    if not path.exists():
        raise FileNotFoundError(
            f"Raw dataset not found: {path}"
        )
    raw_sha256 = calculate_sha256(path)

    if raw_sha256 != EXPECTED_RAW_SHA256:
        raise ValueError(
            "Raw dataset SHA-256 dose not match the approved baseline.\n"
            f"Expected: {EXPECTED_RAW_SHA256}\n"
            f"Actual: {raw_sha256}"
        )

    return raw_sha256

#2. Load raw dataset
def load_raw_data(path: Path) -> pd.DataFrame:

    df = pd.read_csv(path)

    expected_columns = ["Datetime", "AEP_MW"]

    if list(df.columns) != expected_columns:
        raise ValueError(
            "Unexpected raw dataset schema.\n"
            f"Expected columns: {expected_columns}\n"
            f"Actual columns:   {list(df.columns)}"
        )
    return df


#3. Validation and normalize raw data
def normalize_raw_data(
        df_raw: pd.DataFrame,
) -> pd.DataFrame:

    df_work = df_raw.copy()

    #Strict datetime parsing
    try:
        df_work["Datetime"] = pd.to_datetime(
            df_work["Datetime"],
            format=DATETIME_FORMAT,
            errors="raise",
        )
    except (ValueError, TypeError) as exc:
        raise RuntimeError(
            "Datetime parsing failed."
        ) from exc

    # Phase 1 contract requires datetime64[ns]
    df_work["Datetime"] = (
        df_work["Datetime"].astype("datetime64[ns]")
    )

    if df_work["Datetime"].isna().any():
        raise ValueError(
            "Datetime contains NaT after parsing."
        )

    if str(df_work["Datetime"].dtype) != "datetime64[ns]":
        raise TypeError(
            "Datetime dtype is not datetime64[ns]."
        )

    # Dataset remains timezone-naive
    if df_work["Datetime"].dt.tz is not None:
        raise ValueError("Datetime must remain timezone-naive.")

    # Target conversion
    df_work["AEP_MW"] = pd.to_numeric(
        df_work["AEP_MW"],
        errors="raise",
    )

    if df_work["AEP_MW"].isna().any():
        raise ValueError("Raw AEP_MW contains missing value.")

    if (df_work["AEP_MW"] <= 0).any():
        raise ValueError("Raw AEP_MW contains non-positive values.")

    # Stable chronological sort
    df_work = (
        df_work
        .sort_values(
            "Datetime",
            ascending=True,
            kind="stable",
        )
        .reset_index(drop=True)
    )

    if not df_work["Datetime"].is_monotonic_increasing:
        raise ValueError(
            "Datetime is not chronologically sorted."
        )
    return df_work

#4. Aggregate duplicate timestamps
def aggregate_duplicate_timestamps(

    df_work: pd.DataFrame,

) -> pd.DataFrame:

    """

    Aggregate duplicate timestamps using mean AEP_MW.

    source_count records how many raw observations contributed

    to each timestamp.

    """

    duplicate_mask = df_work["Datetime"].duplicated(

        keep=False

    )

    duplicate_rows = df_work.loc[duplicate_mask]

    duplicate_timestamp_count = (

        duplicate_rows["Datetime"].nunique()

    )

    if duplicate_timestamp_count != EXPECTED_DUPLICATE_TIMESTAMPS:

        raise ValueError(

            "Unexpected duplicate timestamp count.\n"

            f"Expected: {EXPECTED_DUPLICATE_TIMESTAMPS}\n"

            f"Actual:   {duplicate_timestamp_count}"

        )

    df_aggregated = (

        df_work

        .groupby(

            "Datetime",

            as_index=False,

            sort=True,

        )

        .agg(

            AEP_MW=("AEP_MW", "mean"),

            source_count=("AEP_MW", "size"),

        )

    )

    df_aggregated["quality_flag"] = "observed"

    df_aggregated.loc[

        df_aggregated["source_count"] > 1,

        "quality_flag",

    ] = "duplicate_aggregated"

    # Source conservation before reindex

    if df_aggregated["source_count"].sum() != len(df_work):

        raise ValueError(

            "Source conservation failed after duplicate aggregation."

        )

    if df_aggregated["Datetime"].duplicated().any():

        raise ValueError(

            "Duplicate timestamps remain after aggregation."

        )

    return df_aggregated

# ============================================================

# 5. Reindex to complete hourly timeline

# ============================================================

def reindex_hourly_timeline(

    df_aggregated: pd.DataFrame,

) -> pd.DataFrame:

    """

    Reindex to a continuous hourly timeline.

    Missing timestamps are inserted with:

    - AEP_MW = NaN

    - source_count = 0

    - quality_flag = missing_timestamp

    No target interpolation or filling is performed.

    """

    complete_hourly_index = pd.date_range(

        start=df_aggregated["Datetime"].min(),

        end=df_aggregated["Datetime"].max(),

        freq="h",

    )

    observed_index = pd.DatetimeIndex(

        df_aggregated["Datetime"]

    )

    missing_timestamps = (

        complete_hourly_index.difference(observed_index)

    )

    if len(missing_timestamps) != EXPECTED_MISSING_TIMESTAMPS:

        raise ValueError(

            "Unexpected missing timestamp count.\n"

            f"Expected: {EXPECTED_MISSING_TIMESTAMPS}\n"

            f"Actual:   {len(missing_timestamps)}"

        )

    df_prepared = (

        df_aggregated

        .set_index("Datetime")

        .reindex(complete_hourly_index)

        .rename_axis("Datetime")

        .reset_index()

    )

    # Identify timestamps inserted by reindexing.

    # source_count is safer than using AEP_MW because it directly

    # identifies rows that did not exist in the observed timeline.

    missing_timestamp_mask = (

        df_prepared["source_count"].isna()

    )

    if (

        missing_timestamp_mask.sum()

        != EXPECTED_MISSING_TIMESTAMPS

    ):

        raise ValueError(

            "Inserted timestamp count does not match expectation."

        )

    df_prepared.loc[

        missing_timestamp_mask,

        "source_count",

    ] = 0

    df_prepared.loc[

        missing_timestamp_mask,

        "quality_flag",

    ] = "missing_timestamp"

    df_prepared["source_count"] = (

        df_prepared["source_count"].astype("int64")

    )

    return df_prepared

# ============================================================

# 6. Final prepared-data validation

# ============================================================

def validate_prepared_data(

    df_prepared: pd.DataFrame,

) -> None:

    """Validate the complete Phase 1 output contract."""

    expected_columns = [

        "Datetime",

        "AEP_MW",

        "source_count",

        "quality_flag",

    ]

    if list(df_prepared.columns) != expected_columns:

        raise ValueError(

            "Unexpected prepared dataset schema."

        )

    if len(df_prepared) != EXPECTED_PREPARED_ROWS:

        raise ValueError(

            "Unexpected prepared row count.\n"

            f"Expected: {EXPECTED_PREPARED_ROWS}\n"

            f"Actual:   {len(df_prepared)}"

        )

    if (

        df_prepared["Datetime"].nunique()

        != EXPECTED_PREPARED_ROWS

    ):

        raise ValueError(

            "Datetime is not unique."

        )

    if df_prepared["Datetime"].duplicated().any():

        raise ValueError(

            "Prepared data contains duplicate timestamps."

        )

    if not df_prepared["Datetime"].is_monotonic_increasing:

        raise ValueError(

            "Prepared timeline is not increasing."

        )

    hourly_continuity = (

        df_prepared["Datetime"]

        .diff()

        .dropna()

        .eq(pd.Timedelta(hours=1))

        .all()

    )

    if not hourly_continuity:

        raise ValueError(

            "Prepared timeline is not continuous hourly data."

        )

    if str(df_prepared["Datetime"].dtype) != "datetime64[ns]":

        raise TypeError(

            "Prepared Datetime dtype is not datetime64[ns]."

        )

    if df_prepared["Datetime"].dt.tz is not None:

        raise ValueError(

            "Prepared Datetime must remain timezone-naive."

        )

    # Missing target contract

    if (

        df_prepared["AEP_MW"].isna().sum()

        != EXPECTED_MISSING_TIMESTAMPS

    ):

        raise ValueError(

            "Unexpected number of missing AEP_MW values."

        )

    # source_count contract

    source_count_expected = {

        0: 27,

        1: 121_265,

        2: 4,

    }

    source_count_actual = (

        df_prepared["source_count"]

        .value_counts()

        .to_dict()

    )

    if source_count_actual != source_count_expected:

        raise ValueError(

            "source_count distribution does not match contract.\n"

            f"Expected: {source_count_expected}\n"

            f"Actual:   {source_count_actual}"

        )

    # quality_flag contract

    quality_flag_expected = {

        "observed": 121_265,

        "missing_timestamp": 27,

        "duplicate_aggregated": 4,

    }

    quality_flag_actual = (

        df_prepared["quality_flag"]

        .value_counts()

        .to_dict()

    )

    if quality_flag_actual != quality_flag_expected:

        raise ValueError(

            "quality_flag distribution does not match contract.\n"

            f"Expected: {quality_flag_expected}\n"

            f"Actual:   {quality_flag_actual}"

        )

    # Source conservation

    if (

        df_prepared["source_count"].sum()

        != EXPECTED_RAW_ROWS

    ):

        raise ValueError(

            "Source conservation failed."

        )

    # Missing timestamp contract

    missing_rows = df_prepared.loc[

        df_prepared["quality_flag"]

        == "missing_timestamp"

    ]

    if not missing_rows["AEP_MW"].isna().all():

        raise ValueError(

            "Missing timestamps contain fabricated target values."

        )

    if not (missing_rows["source_count"] == 0).all():

        raise ValueError(

            "Missing timestamps must have source_count = 0."

        )

# ============================================================

# 7. Main preparation function

# ============================================================

def prepare_aep_data(

    raw_path: Path,

) -> tuple[pd.DataFrame, dict]:

    """

    Run the complete Phase 1 data-preparation pipeline.

    Returns

    -------

    df_prepared:

        Prepared hourly dataset.

    audit:

        Summary of Phase 1 data-quality results.

    """

    raw_path = Path(raw_path)

    raw_sha256_before = validate_raw_file(raw_path)

    df_raw = load_raw_data(raw_path)

    sorted_before = False

    # Determine actual raw chronological state for audit.

    raw_datetime_for_audit = pd.to_datetime(

        df_raw["Datetime"],

        format=DATETIME_FORMAT,

        errors="raise",

    )

    sorted_before = (

        raw_datetime_for_audit.is_monotonic_increasing

    )

    raw_target_for_audit = pd.to_numeric(
        df_raw["AEP_MW"],
        errors="raise",
    )

    raw_duplicate_mask = raw_datetime_for_audit.duplicated(
        keep=False,
    )

    duplicate_rows_before = int(raw_duplicate_mask.sum())
    duplicate_timestamps_before = int(
        raw_datetime_for_audit.loc[raw_duplicate_mask].nunique()
    )

    df_work = normalize_raw_data(df_raw)

    df_aggregated = aggregate_duplicate_timestamps(

        df_work

    )

    complete_hourly_index_for_audit = pd.date_range(
        start=df_aggregated["Datetime"].min(),
        end=df_aggregated["Datetime"].max(),
        freq="h",
    )

    missing_hourly_timestamps_before = int(
        len(
            complete_hourly_index_for_audit.difference(
                pd.DatetimeIndex(df_aggregated["Datetime"])
            )
        )
    )

    df_prepared = reindex_hourly_timeline(

        df_aggregated

    )

    validate_prepared_data(df_prepared)

    # Raw dataset must remain unchanged after processing.

    raw_sha256_after = calculate_sha256(raw_path)

    if raw_sha256_after != raw_sha256_before:

        raise ValueError(

            "Raw dataset changed during processing."

        )

    if raw_sha256_after != EXPECTED_RAW_SHA256:

        raise ValueError(

            "Raw dataset no longer matches approved SHA-256."

        )

    audit = {

        "phase": "phase_01_data_preparation",

        "raw_rows": len(df_raw),

        "raw_missing_AEP_MW": int(
            raw_target_for_audit.isna().sum()
        ),

        "raw_non_positive_AEP_MW": int(
            (raw_target_for_audit <= 0).sum()
        ),

        "duplicate_rows_before": duplicate_rows_before,

        "duplicate_timestamps_before": duplicate_timestamps_before,

        "missing_hourly_timestamps_before": (
            missing_hourly_timestamps_before
        ),

        "prepared_rows": len(df_prepared),

        "unique_timestamps": int(

            df_prepared["Datetime"].nunique()

        ),

        "prepared_time_start": df_prepared["Datetime"].min().strftime(
            DATETIME_FORMAT
        ),

        "prepared_time_end": df_prepared["Datetime"].max().strftime(
            DATETIME_FORMAT
        ),

        "duplicate_timestamps_after": int(

            df_prepared["Datetime"].duplicated().sum()

        ),

        "missing_AEP_MW": int(

            df_prepared["AEP_MW"].isna().sum()

        ),

        "source_count_0": int(

            (df_prepared["source_count"] == 0).sum()

        ),

        "source_count_1": int(

            (df_prepared["source_count"] == 1).sum()

        ),

        "source_count_2": int(

            (df_prepared["source_count"] == 2).sum()

        ),

        "sum_source_count": int(

            df_prepared["source_count"].sum()

        ),

        "raw_chronologically_sorted_before": bool(

            sorted_before

        ),

        "timeline_continuous_hourly": True,

        "timezone_policy": "timezone-naive",

        "raw_sha256_before": raw_sha256_before,

        "raw_sha256_after": raw_sha256_after,

        "status": "PASS",

    }

    return df_prepared, audit

# ============================================================

# 8. Save processed dataset

# ============================================================

def save_prepared_data(

    df_prepared: pd.DataFrame,

    output_path: Path,

) -> None:

    """Save the prepared dataset using the approved datetime format."""

    output_path = Path(output_path)

    output_path.parent.mkdir(

        parents=True,

        exist_ok=True,

    )

    df_prepared.to_csv(

        output_path,

        index=False,

        date_format=DATETIME_FORMAT,
    )

# ============================================================
# 9. Lưu audit result
# ============================================================

def save_audit(
    audit: dict,
    output_path: Path,
) -> None:
    """
    Lưu kết quả audit của Phase 1 dưới dạng JSON.

    File JSON dùng để ghi lại các bằng chứng quan trọng như:
    - số dòng raw
    - số dòng prepared
    - số timestamp bị thiếu
    - source_count
    - SHA-256
    - trạng thái PASS
    """

    output_path = Path(output_path)

    # Tự tạo thư mục outputs/results nếu chưa tồn tại
    output_path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    with output_path.open(
        "w",
        encoding="utf-8",
    ) as file:
        json.dump(
            audit,
            file,
            indent=2,
            ensure_ascii=False,
        )


# ============================================================
# 10. Kiểm tra file CSV sau khi serialize
# ============================================================

def validate_saved_dataset(
    output_path: Path,
) -> None:
    """
    Đọc lại processed CSV sau khi lưu và kiểm tra lại.

    Mục đích:
    Không chỉ kiểm tra dataframe trong RAM mà còn đảm bảo
    file CSV thực tế trên ổ đĩa có thể được đọc lại đúng.
    """

    output_path = Path(output_path)

    if not output_path.exists():
        raise FileNotFoundError(
            f"Không tìm thấy processed dataset: {output_path}"
        )

    df_saved = pd.read_csv(output_path)

    # Parse lại Datetime từ CSV
    df_saved["Datetime"] = pd.to_datetime(
        df_saved["Datetime"],
        format=DATETIME_FORMAT,
        errors="raise",
    ).astype("datetime64[ns]")

    # Đảm bảo các cột số giữ đúng kiểu dữ liệu cần thiết
    df_saved["AEP_MW"] = pd.to_numeric(
        df_saved["AEP_MW"],
        errors="raise",
    )

    df_saved["source_count"] = pd.to_numeric(
        df_saved["source_count"],
        errors="raise",
    ).astype("int64")

    # Dùng lại validation chính thức của Phase 1
    validate_prepared_data(df_saved)


# ============================================================
# 11. Chạy toàn bộ Phase 1 và tạo artifact
# ============================================================

def run_phase_01(
    raw_path: Path = Path(
        "datasets/raw/AEP_hourly.csv"
    ),
    processed_path: Path = Path(
        "datasets/processed/aep_hourly_prepared.csv"
    ),
    audit_path: Path = Path(
        "outputs/results/phase_01_data_quality.json"
    ),
) -> dict:
    """
    Chạy toàn bộ Phase 1 từ raw dataset đến artifact cuối.

    Luồng:
    raw dataset
        -> data preparation
        -> validation
        -> processed CSV
        -> audit JSON
        -> kiểm tra lại CSV đã lưu
    """

    # Chạy pipeline Data Preparation
    df_prepared, audit = prepare_aep_data(
        raw_path
    )

    # Lưu processed dataset
    save_prepared_data(
        df_prepared,
        processed_path,
    )

    # Lưu audit result
    save_audit(
        audit,
        audit_path,
    )

    # Đọc lại CSV đã lưu để đảm bảo artifact thực tế hợp lệ
    validate_saved_dataset(
        processed_path
    )

    return audit


# ============================================================
# 12. Entry point khi chạy file trực tiếp
# ============================================================

if __name__ == "__main__":

    audit = run_phase_01()

    print(
        json.dumps(
            audit,
            indent=2,
            ensure_ascii=False,
        )
    )

    print("\nPhase 1 artifacts: PASS")
