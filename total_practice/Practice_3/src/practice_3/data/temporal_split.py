from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.model_selection import TimeSeriesSplit

from practice_3.data.supervised_dataset import (
    EXPECTED_USABLE_ROWS,
    SupervisedDataset,
    build_supervised_datasets,
    load_pass_audit,
    validate_phase_03_entry,
    validate_supervised_datasets,
)


APPROVED_VALIDATION_CONFIG = {
    "phase": "phase_04_temporal_split_validation",
    "test_start": "2017-08-03 00:00:00",
    "cv": {
        "strategy": "expanding_window",
        "n_splits": 5,
        "test_size": 2160,
        "gap": 0,
        "max_train_size": None,
    },
    "policies": {
        "shuffle": False,
        "seal_final_test": True,
        "persist_full_split_datasets": False,
    },
}

EXPECTED_CONFIGURATION_NAMES = (
    "lag_only_p24",
    "lag_only_p72",
    "lag_only_p168",
    "lag_rolling_p24",
    "lag_rolling_p72",
    "lag_rolling_p168",
)

EXPECTED_TOP_LEVEL = {
    "train_rows": 108_083,
    "train_start": "2004-10-08 01:00:00",
    "train_end": "2017-08-02 23:00:00",
    "test_rows": 8_592,
    "test_start": "2017-08-03 00:00:00",
    "test_end": "2018-08-03 00:00:00",
    "total_rows": 116_675,
}

EXPECTED_CV_FOLDS = (
    {
        "fold": 1,
        "train_samples": 97_283,
        "validation_samples": 2_160,
        "train_end": "2016-05-02 22:00:00",
        "validation_start": "2016-05-02 23:00:00",
        "validation_end": "2016-07-31 22:00:00",
    },
    {
        "fold": 2,
        "train_samples": 99_443,
        "validation_samples": 2_160,
        "train_end": "2016-07-31 22:00:00",
        "validation_start": "2016-07-31 23:00:00",
        "validation_end": "2016-10-29 22:00:00",
    },
    {
        "fold": 3,
        "train_samples": 101_603,
        "validation_samples": 2_160,
        "train_end": "2016-10-29 22:00:00",
        "validation_start": "2016-10-29 23:00:00",
        "validation_end": "2017-01-27 22:00:00",
    },
    {
        "fold": 4,
        "train_samples": 103_763,
        "validation_samples": 2_160,
        "train_end": "2017-01-27 22:00:00",
        "validation_start": "2017-01-27 23:00:00",
        "validation_end": "2017-05-04 23:00:00",
    },
    {
        "fold": 5,
        "train_samples": 105_923,
        "validation_samples": 2_160,
        "train_end": "2017-05-04 23:00:00",
        "validation_start": "2017-05-05 00:00:00",
        "validation_end": "2017-08-02 23:00:00",
    },
)


@dataclass(frozen=True)
class CVFoldIndices:
    fold: int
    train_indices: np.ndarray
    validation_indices: np.ndarray


@dataclass(frozen=True)
class TemporalSplit:
    train_indices: np.ndarray
    test_indices: np.ndarray
    cv_fold_indices: tuple[CVFoldIndices, ...]
    split_config: dict
    timestamp_index: pd.DatetimeIndex
    configuration_names: tuple[str, ...]


def validate_validation_config(config: dict) -> dict:
    if config != APPROVED_VALIDATION_CONFIG:
        raise ValueError(
            "Phase 4 validation configuration does not match the approved "
            "contract.\n"
            f"Expected: {APPROVED_VALIDATION_CONFIG}\n"
            f"Actual:   {config}"
        )

    return {
        "approved_contract": True,
        "status": "PASS",
    }


def load_validation_config(
    config_path: Path = Path("config/validation.json"),
) -> dict:
    config_path = Path(config_path)
    if not config_path.exists():
        raise FileNotFoundError(
            f"Phase 4 validation configuration not found: {config_path}"
        )

    with config_path.open("r", encoding="utf-8") as file:
        config = json.load(file)

    validate_validation_config(config)
    return config


def validate_phase_04_entry(
    feature_config_path: Path = Path("config/feature_engineering.json"),
    validation_config_path: Path = Path("config/validation.json"),
    phase_03_audit_path: Path = Path(
        "outputs/results/phase_03_supervised_quality.json"
    ),
) -> tuple[dict[str, SupervisedDataset], dict, dict]:
    phase_03_audit = load_pass_audit(
        phase_03_audit_path,
        "phase_03_x_y_preparation",
    )
    validation_config = load_validation_config(validation_config_path)
    _, feature_config, feature_df, phase_03_entry = validate_phase_03_entry(
        config_path=feature_config_path
    )
    datasets, row_loss_audit = build_supervised_datasets(
        feature_df,
        feature_config,
    )
    supervised_audit = validate_supervised_datasets(
        datasets,
        feature_config,
    )

    if phase_03_audit["row_loss"] != row_loss_audit:
        raise ValueError(
            "Saved Phase 3 row-loss audit does not match reconstructed data."
        )
    if (
        phase_03_audit["supervised_datasets"]
        != supervised_audit
    ):
        raise ValueError(
            "Saved Phase 3 supervised audit does not match reconstructed data."
        )

    entry_audit = {
        "phase_01": phase_03_entry["phase_01"],
        "phase_02": phase_03_entry["phase_02"],
        "phase_03": phase_03_audit["status"],
        "phase_03_reconstruction": supervised_audit["status"],
        "validation_config": "PASS",
        "status": "PASS",
    }
    return datasets, validation_config, entry_audit


def get_common_timestamp_index(
    datasets: dict[str, SupervisedDataset],
) -> pd.DatetimeIndex:
    if tuple(datasets) != EXPECTED_CONFIGURATION_NAMES:
        raise ValueError("Phase 3 configuration names or order are invalid.")

    reference_index = datasets[EXPECTED_CONFIGURATION_NAMES[0]].timestamp_index
    if len(reference_index) != EXPECTED_USABLE_ROWS:
        raise ValueError(
            "Unexpected Phase 3 common timestamp count: "
            f"expected={EXPECTED_USABLE_ROWS}, actual={len(reference_index)}"
        )
    if not reference_index.is_unique:
        raise ValueError("Phase 3 common timestamp index is not unique.")
    if not reference_index.is_monotonic_increasing:
        raise ValueError(
            "Phase 3 common timestamp index is not chronologically ordered."
        )

    for name in EXPECTED_CONFIGURATION_NAMES[1:]:
        if not datasets[name].timestamp_index.equals(reference_index):
            raise ValueError(
                f"Configuration {name} does not use the common timestamp index."
            )

    return reference_index.copy()


def readonly_indices(values: np.ndarray) -> np.ndarray:
    result = np.asarray(values, dtype=np.int64).copy()
    result.setflags(write=False)
    return result


def create_top_level_indices(
    timestamp_index: pd.DatetimeIndex,
    config: dict,
) -> tuple[np.ndarray, np.ndarray, dict]:
    validate_validation_config(config)
    cutoff = pd.Timestamp(config["test_start"])
    train_indices = readonly_indices(
        np.flatnonzero(timestamp_index < cutoff)
    )
    test_indices = readonly_indices(
        np.flatnonzero(timestamp_index >= cutoff)
    )

    if len(train_indices) == 0 or len(test_indices) == 0:
        raise ValueError("Temporal split produced an empty train or test set.")

    overlap = np.intersect1d(train_indices, test_indices)
    union = np.sort(np.concatenate((train_indices, test_indices)))
    expected_union = np.arange(len(timestamp_index), dtype=np.int64)

    if overlap.size:
        raise ValueError("Top-level train and test indices overlap.")
    if not np.array_equal(union, expected_union):
        raise ValueError("Top-level train/test union is incomplete.")
    if timestamp_index[train_indices[-1]] >= timestamp_index[test_indices[0]]:
        raise ValueError("Top-level split violates chronological order.")

    audit = {
        "train_rows": len(train_indices),
        "train_start": str(timestamp_index[train_indices[0]]),
        "train_end": str(timestamp_index[train_indices[-1]]),
        "test_rows": len(test_indices),
        "test_start": str(timestamp_index[test_indices[0]]),
        "test_end": str(timestamp_index[test_indices[-1]]),
        "total_rows": len(timestamp_index),
        "train_test_disjoint": True,
        "train_test_complete_union": True,
        "chronological_boundary": True,
        "status": "PASS",
    }

    actual = {key: audit[key] for key in EXPECTED_TOP_LEVEL}
    if actual != EXPECTED_TOP_LEVEL:
        raise ValueError(
            "Phase 4 top-level split acceptance values changed.\n"
            f"Expected: {EXPECTED_TOP_LEVEL}\n"
            f"Actual:   {actual}"
        )

    return train_indices, test_indices, audit


def create_cv_fold_indices(
    timestamp_index: pd.DatetimeIndex,
    train_indices: np.ndarray,
    test_indices: np.ndarray,
    config: dict,
) -> tuple[tuple[CVFoldIndices, ...], dict]:
    cv_config = config["cv"]
    splitter = TimeSeriesSplit(
        n_splits=int(cv_config["n_splits"]),
        test_size=int(cv_config["test_size"]),
        gap=int(cv_config["gap"]),
        max_train_size=cv_config["max_train_size"],
    )

    folds = []
    fold_audits = []
    validation_sets = []

    for fold_number, (local_train, local_validation) in enumerate(
        splitter.split(train_indices),
        start=1,
    ):
        fold_train = readonly_indices(train_indices[local_train])
        fold_validation = readonly_indices(train_indices[local_validation])

        if fold_train[-1] >= fold_validation[0]:
            raise ValueError(
                f"CV fold {fold_number} violates chronological order."
            )
        if np.intersect1d(fold_train, fold_validation).size:
            raise ValueError(f"CV fold {fold_number} contains overlap.")
        if np.intersect1d(fold_train, test_indices).size:
            raise ValueError(
                f"Final test appears in CV train fold {fold_number}."
            )
        if np.intersect1d(fold_validation, test_indices).size:
            raise ValueError(
                f"Final test appears in CV validation fold {fold_number}."
            )

        folds.append(
            CVFoldIndices(
                fold=fold_number,
                train_indices=fold_train,
                validation_indices=fold_validation,
            )
        )
        validation_sets.append(fold_validation)
        fold_audits.append(
            {
                "fold": fold_number,
                "train_samples": len(fold_train),
                "validation_samples": len(fold_validation),
                "train_start": str(timestamp_index[fold_train[0]]),
                "train_end": str(timestamp_index[fold_train[-1]]),
                "validation_start": str(
                    timestamp_index[fold_validation[0]]
                ),
                "validation_end": str(
                    timestamp_index[fold_validation[-1]]
                ),
            }
        )

    if len(folds) != int(cv_config["n_splits"]):
        raise ValueError("Unexpected number of TimeSeriesSplit folds.")

    for previous, current in zip(folds, folds[1:]):
        if len(current.train_indices) <= len(previous.train_indices):
            raise ValueError("CV training windows are not expanding.")
        if not np.array_equal(
            current.train_indices[: len(previous.train_indices)],
            previous.train_indices,
        ):
            raise ValueError("CV training windows do not preserve history.")

    combined_validation = np.concatenate(validation_sets)
    if len(np.unique(combined_validation)) != len(combined_validation):
        raise ValueError("CV validation folds overlap.")

    acceptance_folds = tuple(
        {
            key: fold[key]
            for key in EXPECTED_CV_FOLDS[index]
        }
        for index, fold in enumerate(fold_audits)
    )
    if acceptance_folds != EXPECTED_CV_FOLDS:
        raise ValueError(
            "Phase 4 CV fold acceptance values changed.\n"
            f"Expected: {EXPECTED_CV_FOLDS}\n"
            f"Actual:   {acceptance_folds}"
        )

    audit = {
        "strategy": cv_config["strategy"],
        "n_splits": len(folds),
        "test_size": int(cv_config["test_size"]),
        "gap": int(cv_config["gap"]),
        "max_train_size": cv_config["max_train_size"],
        "folds": fold_audits,
        "training_windows_expand": True,
        "validation_folds_disjoint": True,
        "final_test_excluded": True,
        "status": "PASS",
    }
    return tuple(folds), audit


def validate_shared_indices(
    datasets: dict[str, SupervisedDataset],
    split: TemporalSplit,
) -> dict:
    reference_train = split.timestamp_index[split.train_indices]
    reference_test = split.timestamp_index[split.test_indices]

    configuration_audit = {}
    for name in split.configuration_names:
        dataset = datasets[name]
        if not dataset.timestamp_index.equals(split.timestamp_index):
            raise ValueError(f"Timestamp index drift detected for {name}.")

        train_timestamps = dataset.timestamp_index[split.train_indices]
        test_timestamps = dataset.timestamp_index[split.test_indices]
        if not train_timestamps.equals(reference_train):
            raise ValueError(f"Train index drift detected for {name}.")
        if not test_timestamps.equals(reference_test):
            raise ValueError(f"Test index drift detected for {name}.")
        if not dataset.X.iloc[split.train_indices].index.equals(
            dataset.y.iloc[split.train_indices].index
        ):
            raise ValueError(f"Train X/y alignment failed for {name}.")
        if not dataset.X.iloc[split.test_indices].index.equals(
            dataset.y.iloc[split.test_indices].index
        ):
            raise ValueError(f"Test X/y alignment failed for {name}.")
        if not dataset.X.iloc[split.train_indices].index.equals(
            dataset.aligned_metadata.iloc[split.train_indices].index
        ):
            raise ValueError(f"Train metadata alignment failed for {name}.")
        if not dataset.X.iloc[split.test_indices].index.equals(
            dataset.aligned_metadata.iloc[split.test_indices].index
        ):
            raise ValueError(f"Test metadata alignment failed for {name}.")

        configuration_audit[name] = {
            "train_rows": len(split.train_indices),
            "test_rows": len(split.test_indices),
            "train_test_indices_shared": True,
            "cv_indices_shared": True,
            "alignment": "PASS",
        }

    return {
        "configuration_count": len(configuration_audit),
        "configuration_names": list(split.configuration_names),
        "shared_top_level_indices": True,
        "shared_cv_indices": True,
        "configurations": configuration_audit,
        "status": "PASS",
    }


def build_temporal_split(
    datasets: dict[str, SupervisedDataset],
    config: dict,
) -> tuple[TemporalSplit, dict, dict]:
    timestamp_index = get_common_timestamp_index(datasets)
    train_indices, test_indices, top_level_audit = (
        create_top_level_indices(timestamp_index, config)
    )
    cv_folds, cv_audit = create_cv_fold_indices(
        timestamp_index,
        train_indices,
        test_indices,
        config,
    )
    split = TemporalSplit(
        train_indices=train_indices,
        test_indices=test_indices,
        cv_fold_indices=cv_folds,
        split_config=config,
        timestamp_index=timestamp_index,
        configuration_names=EXPECTED_CONFIGURATION_NAMES,
    )
    validate_shared_indices(datasets, split)
    return split, top_level_audit, cv_audit


def validate_deterministic_split(
    datasets: dict[str, SupervisedDataset],
    config: dict,
    reference_split: TemporalSplit,
) -> dict:
    repeated_split, _, _ = build_temporal_split(datasets, config)

    if not np.array_equal(
        repeated_split.train_indices,
        reference_split.train_indices,
    ):
        raise ValueError("Top-level train split is not deterministic.")
    if not np.array_equal(
        repeated_split.test_indices,
        reference_split.test_indices,
    ):
        raise ValueError("Top-level test split is not deterministic.")

    for reference_fold, repeated_fold in zip(
        reference_split.cv_fold_indices,
        repeated_split.cv_fold_indices,
    ):
        if not np.array_equal(
            reference_fold.train_indices,
            repeated_fold.train_indices,
        ):
            raise ValueError(
                f"CV train fold {reference_fold.fold} is not deterministic."
            )
        if not np.array_equal(
            reference_fold.validation_indices,
            repeated_fold.validation_indices,
        ):
            raise ValueError(
                "CV validation fold "
                f"{reference_fold.fold} is not deterministic."
            )

    return {
        "deterministic_split": True,
        "status": "PASS",
    }


def save_phase_04_audit(
    audit: dict,
    output_path: Path = Path("outputs/results/phase_04_split_audit.json"),
) -> None:
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8") as file:
        json.dump(audit, file, indent=2, ensure_ascii=False)


def run_phase_04(
    feature_config_path: Path = Path("config/feature_engineering.json"),
    validation_config_path: Path = Path("config/validation.json"),
    audit_path: Path = Path("outputs/results/phase_04_split_audit.json"),
) -> tuple[dict[str, SupervisedDataset], TemporalSplit, dict]:
    datasets, config, entry_audit = validate_phase_04_entry(
        feature_config_path=feature_config_path,
        validation_config_path=validation_config_path,
    )
    config_audit = validate_validation_config(config)
    split, top_level_audit, cv_audit = build_temporal_split(
        datasets,
        config,
    )
    shared_audit = validate_shared_indices(datasets, split)
    deterministic_audit = validate_deterministic_split(
        datasets,
        config,
        split,
    )

    audit = {
        "phase": "phase_04_temporal_split_validation",
        "entry_gate": entry_audit,
        "configuration": config_audit,
        "top_level_split": top_level_audit,
        "cross_validation": cv_audit,
        "shared_indices": shared_audit,
        "final_test": {
            "sealed": config["policies"]["seal_final_test"],
            "used_for_feature_selection": False,
            "used_for_tuning": False,
            "used_for_model_selection": False,
            "metrics_computed": False,
            "status": "PASS",
        },
        "determinism": deterministic_audit,
        "full_split_datasets_persisted": config["policies"][
            "persist_full_split_datasets"
        ],
        "status": "PASS",
    }
    save_phase_04_audit(audit, audit_path)
    return datasets, split, audit


if __name__ == "__main__":
    _, _, phase_audit = run_phase_04()
    print(json.dumps(phase_audit, indent=2, ensure_ascii=False))
    print("\nPhase 4 temporal split validation: PASS")
