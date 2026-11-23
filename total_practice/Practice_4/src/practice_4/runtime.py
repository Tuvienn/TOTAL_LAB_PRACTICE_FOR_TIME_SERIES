from __future__ import annotations

import csv
import hashlib
import importlib.metadata
import json
import os
import platform
import random
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import numpy as np


PRACTICE_ROOT = Path(__file__).resolve().parents[2]
FILE_MAP_PATH = PRACTICE_ROOT / "docs/plans/file_map.csv"
FILE_MAP_COLUMNS = [
    "file_id",
    "path",
    "entry_kind",
    "existence",
    "first_stage",
    "owner",
    "responsibility",
    "depends_on",
    "consumers",
    "validation",
]


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, allow_nan=False) + "\n",
        encoding="utf-8",
    )


def load_config(config_path: Path | None = None) -> dict[str, Any]:
    target = config_path or (PRACTICE_ROOT / "config/practice_4_v2.json")
    return json.loads(target.read_text(encoding="utf-8"))


def set_deterministic_seed(seed: int) -> None:
    os.environ["PYTHONHASHSEED"] = str(seed)
    random.seed(seed)
    np.random.seed(seed)
    try:
        import torch

        torch.manual_seed(seed)
        if torch.cuda.is_available():
            torch.cuda.manual_seed(seed)
            torch.cuda.manual_seed_all(seed)
            torch.backends.cudnn.deterministic = True
            torch.backends.cudnn.benchmark = False
    except ImportError:
        pass


def collect_environment(require_cuda: bool = True) -> dict[str, Any]:
    packages = [
        "numpy",
        "pandas",
        "scipy",
        "scikit-learn",
        "statsmodels",
        "xgboost",
        "torch",
        "shap",
        "holidays",
        "matplotlib",
        "seaborn",
        "pytest",
        "requests",
        "nbconvert",
        "ipykernel",
        "tzdata",
    ]
    versions: dict[str, str | None] = {}
    for pkg in packages:
        try:
            versions[pkg] = importlib.metadata.version(pkg)
        except importlib.metadata.PackageNotFoundError:
            versions[pkg] = None

    import torch
    import xgboost as xgb

    cuda_available = bool(torch.cuda.is_available())
    if require_cuda and not cuda_available:
        raise RuntimeError("NVIDIA CUDA GPU is required but torch.cuda.is_available() is False")

    gpu_info: dict[str, Any] = {
        "torch_cuda_available": cuda_available,
        "torch_cuda_version": torch.version.cuda,
        "device_count": int(torch.cuda.device_count()) if cuda_available else 0,
        "device_name": torch.cuda.get_device_name(0) if cuda_available else None,
        "device_capability": list(torch.cuda.get_device_capability(0)) if cuda_available else None,
        "vram_total_mb": round(torch.cuda.get_device_properties(0).total_memory / (1024 ** 2), 1)
        if cuda_available
        else 0.0,
        "xgboost_use_cuda": bool(xgb.build_info().get("USE_CUDA", False)),
        "xgboost_cuda_version": xgb.build_info().get("CUDA_VERSION"),
    }

    return {
        "recorded_at_utc": utc_now(),
        "python": platform.python_version(),
        "platform": platform.platform(),
        "gpu": gpu_info,
        "packages": versions,
    }


def read_file_map(map_path: Path | None = None) -> list[dict[str, str]]:
    target = map_path or FILE_MAP_PATH
    if not target.exists():
        return []
    with target.open("r", encoding="utf-8", newline="") as stream:
        return list(csv.DictReader(stream))


def write_file_map(rows: list[dict[str, str]], map_path: Path | None = None) -> None:
    target = map_path or FILE_MAP_PATH
    target.parent.mkdir(parents=True, exist_ok=True)
    with target.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=FILE_MAP_COLUMNS, lineterminator="\n")
        writer.writeheader()
        for row in rows:
            writer.writerow({col: row.get(col, "") for col in FILE_MAP_COLUMNS})


def upsert_file_map_entries(entries: list[dict[str, str]], map_path: Path | None = None) -> list[dict[str, str]]:
    rows = read_file_map(map_path)
    by_path = {row["path"]: idx for idx, row in enumerate(rows)}
    used_ids = {row["file_id"] for row in rows}
    max_num = 0
    for fid in used_ids:
        if fid.startswith("F") and fid[1:].isdigit():
            max_num = max(max_num, int(fid[1:]))

    for entry in entries:
        rel_path = entry["path"].replace("\\", "/")
        if rel_path in by_path:
            existing = rows[by_path[rel_path]]
            for col in FILE_MAP_COLUMNS:
                if col != "file_id" and col in entry:
                    existing[col] = entry[col]
        else:
            max_num += 1
            new_row = {col: entry.get(col, "") for col in FILE_MAP_COLUMNS}
            new_row["file_id"] = entry.get("file_id") or f"F{max_num:03d}"
            new_row["path"] = rel_path
            rows.append(new_row)
            by_path[rel_path] = len(rows) - 1

    write_file_map(rows, map_path)
    return rows


def sync_file_map_existence(root: Path | None = None, map_path: Path | None = None) -> dict[str, int]:
    base = root or PRACTICE_ROOT
    rows = read_file_map(map_path)
    existing_count = 0
    removed_count = 0
    cleaned: list[dict[str, str]] = []
    for row in rows:
        rel = row["path"]
        if row["entry_kind"] == "FAMILY":
            cleaned.append(row)
            continue
        if (base / rel).exists():
            row["existence"] = "EXISTING"
            existing_count += 1
            cleaned.append(row)
        else:
            removed_count += 1
    write_file_map(cleaned, map_path)
    return {"existing_files": existing_count, "pruned_deleted_entries": removed_count, "total_rows": len(cleaned)}
