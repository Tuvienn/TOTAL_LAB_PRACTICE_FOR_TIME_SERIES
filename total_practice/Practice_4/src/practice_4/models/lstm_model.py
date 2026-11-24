from __future__ import annotations

import copy
import time
from pathlib import Path
from typing import Any

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import torch
from torch import nn
from torch.utils.data import DataLoader, Dataset

from practice_4.analysis.metrics import calculate_metrics
from practice_4.data.preprocessing import inverse_scale_load
from practice_4.runtime import set_deterministic_seed, write_json


class SequenceWindowDataset(Dataset):
    def __init__(
        self,
        full_seq: np.ndarray,
        target_rows: np.ndarray,
        y_scaled: np.ndarray,
        window_len: int,
        col_indices: list[int],
        target_cal: np.ndarray | None = None,
    ):
        self.full_seq = full_seq[:, col_indices].astype(np.float32, copy=False)
        self.target_rows = target_rows.astype(np.int64, copy=False)
        self.y_scaled = y_scaled.astype(np.float32, copy=False)
        self.window_len = int(window_len)
        if target_cal is None:
            self.target_cal = np.zeros((len(self.target_rows), 0), dtype=np.float32)
        else:
            self.target_cal = target_cal.astype(np.float32, copy=False)

    def __len__(self) -> int:
        return len(self.target_rows)

    def __getitem__(self, idx: int) -> tuple[torch.Tensor, torch.Tensor, torch.Tensor]:
        trow = int(self.target_rows[idx])
        window = self.full_seq[trow - self.window_len : trow]
        return (
            torch.from_numpy(window.copy()),
            torch.from_numpy(self.target_cal[idx].copy()),
            torch.tensor(self.y_scaled[idx], dtype=torch.float32),
        )


class MultivariateLSTM(nn.Module):
    def __init__(
        self,
        input_size: int,
        hidden1: int = 64,
        hidden2: int = 32,
        dropout: float = 0.0,
        future_cal_dim: int = 0,
    ):
        super().__init__()
        self.input_size = int(input_size)
        self.hidden1 = int(hidden1)
        self.hidden2 = int(hidden2)
        self.dropout_rate = float(dropout)
        self.future_cal_dim = int(future_cal_dim)
        self.lstm1 = nn.LSTM(input_size, hidden1, batch_first=True)
        self.drop1 = nn.Dropout(dropout) if dropout > 0.0 else nn.Identity()
        self.lstm2 = nn.LSTM(hidden1, hidden2, batch_first=True)
        self.drop2 = nn.Dropout(dropout) if dropout > 0.0 else nn.Identity()
        self.head = nn.Linear(hidden2 + self.future_cal_dim, 1)

    def forward(self, x: torch.Tensor, future_cal: torch.Tensor | None = None) -> torch.Tensor:
        out, _ = self.lstm1(x)
        out = self.drop1(out)
        out, _ = self.lstm2(out)
        out = self.drop2(out[:, -1, :])
        if self.future_cal_dim > 0:
            if future_cal is None or future_cal.shape[-1] != self.future_cal_dim:
                raise ValueError(f"Expected future_cal with dim {self.future_cal_dim}")
            out = torch.cat([out, future_cal], dim=-1)
        return self.head(out).squeeze(-1)


def count_trainable_parameters(model: nn.Module) -> int:
    return int(sum(p.numel() for p in model.parameters() if p.requires_grad))


@torch.no_grad()
def predict_dataset(model: nn.Module, loader: DataLoader, device: torch.device) -> np.ndarray:
    model.eval()
    chunks = []
    for xb, fb, _ in loader:
        xb = xb.to(device, non_blocking=True)
        f_in = fb.to(device, non_blocking=True) if fb.shape[-1] > 0 else None
        chunks.append(model(xb, f_in).detach().cpu().numpy().astype(np.float64))
    return np.concatenate(chunks, axis=0)


@torch.no_grad()
def predict_single_window(
    model: nn.Module,
    window: np.ndarray,
    device: torch.device,
    future_cal: np.ndarray | None = None,
) -> float:
    model.eval()
    tensor = torch.from_numpy(np.asarray(window, dtype=np.float32)[None, ...]).to(device)
    f_tensor = None
    if future_cal is not None and len(future_cal) > 0:
        f_tensor = torch.from_numpy(np.asarray(future_cal, dtype=np.float32)[None, ...]).to(device)
    return float(model(tensor, f_tensor).detach().cpu().item())


def train_single_lstm(
    train_ds: Dataset,
    val_ds: Dataset,
    input_size: int,
    lr: float,
    dropout: float,
    weight_decay: float,
    epochs: int,
    patience: int,
    batch_size: int,
    seed: int,
    device: torch.device,
    future_cal_dim: int = 0,
) -> dict[str, Any]:
    set_deterministic_seed(seed)
    gen = torch.Generator()
    gen.manual_seed(seed)

    train_loader = DataLoader(train_ds, batch_size=batch_size, shuffle=True, generator=gen)
    train_eval_loader = DataLoader(train_ds, batch_size=batch_size * 2, shuffle=False)
    val_loader = DataLoader(val_ds, batch_size=batch_size * 2, shuffle=False)

    model = MultivariateLSTM(
        input_size=input_size,
        hidden1=64,
        hidden2=32,
        dropout=dropout,
        future_cal_dim=future_cal_dim,
    ).to(device)
    optimizer = torch.optim.Adam(model.parameters(), lr=lr, weight_decay=weight_decay)
    scheduler = torch.optim.lr_scheduler.ReduceLROnPlateau(
        optimizer, mode="min", factor=0.5, patience=max(3, patience // 3), min_lr=1e-5
    )
    criterion = nn.MSELoss()

    best_val_loss = float("inf")
    best_epoch = 1
    best_state = copy.deepcopy(model.state_dict())
    no_improve = 0
    history = []
    started = time.perf_counter()

    for epoch in range(1, epochs + 1):
        model.train()
        tr_loss_sum = 0.0
        tr_count = 0
        for xb, fb, yb in train_loader:
            xb = xb.to(device, non_blocking=True)
            f_in = fb.to(device, non_blocking=True) if fb.shape[-1] > 0 else None
            yb = yb.to(device, non_blocking=True)
            optimizer.zero_grad(set_to_none=True)
            pred = model(xb, f_in)
            loss = criterion(pred, yb)
            loss.backward()
            torch.nn.utils.clip_grad_norm_(model.parameters(), max_norm=5.0)
            optimizer.step()
            bs = len(yb)
            tr_loss_sum += float(loss.item()) * bs
            tr_count += bs

        model.eval()
        va_loss_sum = 0.0
        va_count = 0
        with torch.no_grad():
            for xb, fb, yb in val_loader:
                xb = xb.to(device, non_blocking=True)
                f_in = fb.to(device, non_blocking=True) if fb.shape[-1] > 0 else None
                yb = yb.to(device, non_blocking=True)
                pred = model(xb, f_in)
                loss = criterion(pred, yb)
                bs = len(yb)
                va_loss_sum += float(loss.item()) * bs
                va_count += bs

        tr_mse = tr_loss_sum / tr_count
        va_mse = va_loss_sum / va_count
        scheduler.step(va_mse)
        history.append({"epoch": epoch, "train_loss": tr_mse, "val_loss": va_mse, "lr": optimizer.param_groups[0]["lr"]})

        if va_mse < best_val_loss - 1e-9:
            best_val_loss = va_mse
            best_epoch = epoch
            best_state = copy.deepcopy(model.state_dict())
            no_improve = 0
        else:
            no_improve += 1
            if no_improve >= patience:
                break

    elapsed = time.perf_counter() - started
    model.load_state_dict(best_state)
    val_preds_scaled = predict_dataset(model, val_loader, device)
    tr_preds_scaled = predict_dataset(model, train_eval_loader, device)
    return {
        "model": model,
        "state_dict": best_state,
        "best_epoch": int(best_epoch),
        "stop_epoch": int(len(history)),
        "best_val_mse_scaled": float(best_val_loss),
        "restored_train_mse_scaled": float(np.mean((tr_preds_scaled - train_ds.y_scaled) ** 2)),
        "restored_val_mse_scaled": float(np.mean((val_preds_scaled - val_ds.y_scaled) ** 2)),
        "val_preds_scaled": val_preds_scaled,
        "history": history,
        "elapsed_seconds": float(elapsed),
        "param_count": count_trainable_parameters(model),
    }


def run_lstm_stage(
    full_scaled_seq: np.ndarray,
    target_rows: np.ndarray,
    target_cal: np.ndarray,
    y_true: np.ndarray,
    origin_df: pd.DataFrame,
    scaler_state: dict[str, Any],
    config: dict[str, Any],
    artifacts_dir: Path,
    figures_dir: Path,
) -> dict[str, Any]:
    artifacts_dir.mkdir(parents=True, exist_ok=True)
    figures_dir.mkdir(parents=True, exist_ok=True)
    lstm_cfg = config["lstm"]
    device = torch.device(lstm_cfg["device"] if torch.cuda.is_available() else "cpu")
    if device.type != "cuda":
        raise RuntimeError("CUDA GPU required for Stage S7 LSTM training")

    seed = int(config["seed"])
    mean_load = float(scaler_state["mean"][0])
    scale_load = float(scaler_state["scale"][0])
    y_scaled = ((y_true - mean_load) / scale_load).astype(np.float32)

    eligible = origin_df[origin_df["eligible"]].reset_index(drop=True)
    train_mask = (eligible["split"] == "train").to_numpy()
    val_mask = (eligible["split"] == "validation").to_numpy()
    val_all = origin_df[origin_df["split"] == "validation"]
    n_missing = int((val_all["exclusion_reason"] == "missing_truth").sum())
    n_invalid = int((val_all["exclusion_reason"] == "invalid_context").sum())

    tr_targets, va_targets = target_rows[train_mask], target_rows[val_mask]
    tr_tcal, va_tcal = target_cal[train_mask], target_cal[val_mask]
    tr_y_s, va_y_s = y_scaled[train_mask], y_scaled[val_mask]
    va_y_orig = y_true[val_mask]

    n_total_cols = full_scaled_seq.shape[1]
    n_cal_cols = int(target_cal.shape[1])
    variant_specs = {
        "LSTM_24h_load_only": {"window_len": 24, "cols": [0], "future_cal_dim": 0},
        "LSTM_24h_core": {"window_len": 24, "cols": [0, 1, 2, 3], "future_cal_dim": 0},
        "LSTM_24h_cal": {"window_len": 24, "cols": list(range(n_total_cols)), "future_cal_dim": n_cal_cols},
        "LSTM_168h_diag": {"window_len": 168, "cols": list(range(n_total_cols)), "future_cal_dim": n_cal_cols},
    }

    trial_records = []
    histories = []
    best_per_variant: dict[str, dict[str, Any]] = {}

    for variant_name, spec in variant_specs.items():
        fdim = int(spec["future_cal_dim"])
        tr_ds = SequenceWindowDataset(
            full_scaled_seq, tr_targets, tr_y_s, spec["window_len"], spec["cols"], tr_tcal if fdim > 0 else None
        )
        va_ds = SequenceWindowDataset(
            full_scaled_seq, va_targets, va_y_s, spec["window_len"], spec["cols"], va_tcal if fdim > 0 else None
        )
        # Fair tuning budget: evaluate the exact same hyperparameter grid for all 4 variants
        grid_to_run = lstm_cfg["grid"]
        best_run = None

        for hp in grid_to_run:
            out = train_single_lstm(
                tr_ds,
                va_ds,
                input_size=len(spec["cols"]),
                lr=float(hp["lr"]),
                dropout=float(hp["dropout"]),
                weight_decay=float(hp["weight_decay"]),
                epochs=int(lstm_cfg["epochs"]),
                patience=int(lstm_cfg["patience"]),
                batch_size=int(lstm_cfg["batch_size"]),
                seed=seed,
                device=device,
                future_cal_dim=fdim,
            )
            preds_orig = inverse_scale_load(out["val_preds_scaled"], scaler_state)
            scores = calculate_metrics(va_y_orig, preds_orig, n_missing, n_invalid)
            rec = {
                "variant": variant_name,
                "trial_id": f"{variant_name}_{hp['trial_id']}",
                "window_len": spec["window_len"],
                "input_size": len(spec["cols"]),
                "future_cal_dim": fdim,
                "lr": float(hp["lr"]),
                "dropout": float(hp["dropout"]),
                "weight_decay": float(hp["weight_decay"]),
                "param_count": out["param_count"],
                "best_epoch": out["best_epoch"],
                "stop_epoch": out["stop_epoch"],
                "elapsed_seconds": out["elapsed_seconds"],
                "restored_train_mse_scaled": out["restored_train_mse_scaled"],
                "restored_val_mse_scaled": out["restored_val_mse_scaled"],
                **scores,
            }
            trial_records.append(rec)
            for row in out["history"]:
                histories.append({"variant": variant_name, "trial_id": rec["trial_id"], **row})

            if best_run is None or scores["rmse_kw"] < best_run["record"]["rmse_kw"]:
                best_run = {"record": rec, "out": out, "preds_orig": preds_orig, "spec": spec, "hp": hp}

        assert best_run is not None
        best_per_variant[variant_name] = best_run

    trials_df = pd.DataFrame(trial_records).sort_values("rmse_kw").reset_index(drop=True)
    trials_df.to_csv(artifacts_dir / "trials.csv", index=False)
    pd.DataFrame(histories).to_csv(artifacts_dir / "training_history.csv", index=False)

    winner_name = min(best_per_variant, key=lambda k: best_per_variant[k]["record"]["rmse_kw"])
    winner = best_per_variant[winner_name]

    saved_checkpoints = {}
    for save_key, vname in (("lstm_best", winner_name), ("lstm_core", "LSTM_24h_core")):
        entry = best_per_variant[vname]
        fdim = int(entry["spec"]["future_cal_dim"])
        ckpt_path = artifacts_dir / f"{save_key}.pt"
        torch.save(entry["out"]["state_dict"], ckpt_path)
        meta = {
            "variant": vname,
            "window_len": entry["spec"]["window_len"],
            "col_indices": entry["spec"]["cols"],
            "input_size": len(entry["spec"]["cols"]),
            "future_cal_dim": fdim,
            "hidden1": 64,
            "hidden2": 32,
            "dropout": float(entry["hp"]["dropout"]),
            "param_count": entry["out"]["param_count"],
            "best_epoch": entry["out"]["best_epoch"],
            "lr": float(entry["hp"]["lr"]),
            "weight_decay": float(entry["hp"]["weight_decay"]),
        }
        write_json(artifacts_dir / f"{save_key}_arch.json", meta)

        reloaded = MultivariateLSTM(
            input_size=meta["input_size"],
            hidden1=meta["hidden1"],
            hidden2=meta["hidden2"],
            dropout=meta["dropout"],
            future_cal_dim=fdim,
        ).to(device)
        reloaded.load_state_dict(torch.load(ckpt_path, map_location=device, weights_only=True))
        va_ds = SequenceWindowDataset(
            full_scaled_seq,
            va_targets,
            va_y_s,
            meta["window_len"],
            meta["col_indices"],
            va_tcal if fdim > 0 else None,
        )
        reloaded_batch = inverse_scale_load(
            predict_dataset(reloaded, DataLoader(va_ds, batch_size=256, shuffle=False), device),
            scaler_state,
        )
        batch_diff = float(np.max(np.abs(reloaded_batch - entry["preds_orig"])))
        w0 = full_scaled_seq[int(va_targets[0]) - meta["window_len"] : int(va_targets[0]), meta["col_indices"]]
        f0 = va_tcal[0] if fdim > 0 else None
        single_pred = float(
            inverse_scale_load(np.array([predict_single_window(reloaded, w0, device, f0)]), scaler_state)[0]
        )
        single_diff = abs(single_pred - float(reloaded_batch[0]))
        if batch_diff > 1e-2 or single_diff > 1e-2:
            raise ValueError(f"LSTM reload parity failure ({save_key}): batch={batch_diff}, single={single_diff}")
        saved_checkpoints[save_key] = {
            "variant": vname,
            "ckpt_path": str(ckpt_path),
            "arch_path": str(artifacts_dir / f"{save_key}_arch.json"),
            "reload_batch_max_diff": batch_diff,
            "reload_single_diff": single_diff,
        }

    seed_rows = []
    win_spec = winner["spec"]
    win_hp = winner["hp"]
    win_fdim = int(win_spec["future_cal_dim"])
    tr_win = SequenceWindowDataset(
        full_scaled_seq,
        tr_targets,
        tr_y_s,
        win_spec["window_len"],
        win_spec["cols"],
        tr_tcal if win_fdim > 0 else None,
    )
    va_win = SequenceWindowDataset(
        full_scaled_seq,
        va_targets,
        va_y_s,
        win_spec["window_len"],
        win_spec["cols"],
        va_tcal if win_fdim > 0 else None,
    )
    for s in lstm_cfg["seeds_stability"]:
        if int(s) == seed:
            seed_rows.append(
                {
                    "seed": int(s),
                    "best_epoch": winner["record"]["best_epoch"],
                    "mae_kw": winner["record"]["mae_kw"],
                    "rmse_kw": winner["record"]["rmse_kw"],
                    "mape_percent": winner["record"]["mape_percent"],
                }
            )
            continue
        out_s = train_single_lstm(
            tr_win,
            va_win,
            input_size=len(win_spec["cols"]),
            lr=float(win_hp["lr"]),
            dropout=float(win_hp["dropout"]),
            weight_decay=float(win_hp["weight_decay"]),
            epochs=int(lstm_cfg["epochs"]),
            patience=int(lstm_cfg["patience"]),
            batch_size=int(lstm_cfg["batch_size"]),
            seed=int(s),
            device=device,
            future_cal_dim=win_fdim,
        )
        preds_s = inverse_scale_load(out_s["val_preds_scaled"], scaler_state)
        sc = calculate_metrics(va_y_orig, preds_s, n_missing, n_invalid)
        seed_rows.append(
            {
                "seed": int(s),
                "best_epoch": out_s["best_epoch"],
                "mae_kw": sc["mae_kw"],
                "rmse_kw": sc["rmse_kw"],
                "mape_percent": sc["mape_percent"],
            }
        )
    seed_df = pd.DataFrame(seed_rows)
    seed_df.to_csv(artifacts_dir / "seed_stability.csv", index=False)

    val_table = eligible.loc[
        val_mask, ["target_row", "origin_timestamp_utc", "target_timestamp_utc", "y_true"]
    ].copy()
    for vname, entry in best_per_variant.items():
        val_table[vname] = entry["preds_orig"]
    val_table.to_csv(artifacts_dir / "validation_predictions.csv", index=False)

    fig, axes = plt.subplots(2, 2, figsize=(12, 8))
    hist_df = pd.DataFrame(histories)
    for ax, vname in zip(axes.ravel(), variant_specs.keys()):
        best_tid = best_per_variant[vname]["record"]["trial_id"]
        sub = hist_df[hist_df["trial_id"] == best_tid]
        ax.plot(sub["epoch"], sub["train_loss"], label="Train MSE (scaled)")
        ax.plot(sub["epoch"], sub["val_loss"], label="Val MSE (scaled)")
        ax.axvline(best_per_variant[vname]["record"]["best_epoch"], color="gray", ls="--", label="Best epoch")
        ax.set_title(f"{vname} ({best_tid})")
        ax.set_xlabel("Epoch")
        ax.set_ylabel("Scaled MSE")
        ax.set_yscale("log")
        ax.legend(fontsize=8)
    fig.tight_layout()
    fig.savefig(figures_dir / "lstm_learning_curves.png", dpi=130)
    plt.close(fig)

    return {
        "device": f"{device} ({torch.cuda.get_device_name(0)})",
        "winner_variant": winner_name,
        "variants_summary": [best_per_variant[k]["record"] for k in variant_specs.keys()],
        "seed_stability": seed_rows,
        "checkpoints": saved_checkpoints,
    }


def format_lstm_markdown(res: dict[str, Any], unit: str = "kW") -> str:
    lines = [
        "# Stage S7 — PyTorch CUDA LSTM Findings & Ablation (v2)",
        "",
        f"- **Device:** `{res['device']}` (zero `np.repeat(64)` workaround; native `batch=1` & batched inference verified)",
        f"- **Selected Winning LSTM Variant:** **`{res['winner_variant']}`**",
        "",
        "## 1. Variant & Ablation Comparison (Validation)",
        "",
        f"| Variant | Window | Seq Dim | Target Cal (t+1) | Best Trial | Params | Best/Stop Epoch | Fit (s) | Train MSE (scaled) | Val MSE (scaled) | MAE ({unit}) | RMSE ({unit}) | MAPE (%) |",
        "|---|---:|---:|---:|---|---:|---|---:|---:|---:|---:|---:|---:|",
    ]
    for r in res["variants_summary"]:
        trial_short = r["trial_id"].replace(f"{r['variant']}_", "")
        lines.append(
            f"| `{r['variant']}` | {r['window_len']}h | {r['input_size']} | {r.get('future_cal_dim', 0)} | `{trial_short}` | {r['param_count']:,} | "
            f"{r['best_epoch']}/{r['stop_epoch']} | {r['elapsed_seconds']:.2f} | "
            f"{r['restored_train_mse_scaled']:.6f} | {r['restored_val_mse_scaled']:.6f} | "
            f"{r['mae_kw']:,.2f} | {r['rmse_kw']:,.2f} | {r['mape_percent']:.4f} |"
        )
    lines += [
        "",
        f"## 2. Multi-Seed Stability (`{res['winner_variant']}`)",
        "",
        f"| Seed | Best Epoch | MAE ({unit}) | RMSE ({unit}) | MAPE (%) |",
        "|---:|---:|---:|---:|---:|",
    ]
    rmses = []
    for row in res["seed_stability"]:
        rmses.append(row["rmse_kw"])
        lines.append(
            f"| {row['seed']} | {row['best_epoch']} | {row['mae_kw']:,.2f} | {row['rmse_kw']:,.2f} | {row['mape_percent']:.4f} |"
        )
    lines += [
        "",
        f"- Seed RMSE Mean ± Std: **{np.mean(rmses):,.2f} ± {np.std(rmses):,.2f} {unit}**",
        "",
    ]
    return "\n".join(lines)
