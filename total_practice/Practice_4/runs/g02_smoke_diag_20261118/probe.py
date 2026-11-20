
import os
from pathlib import Path
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parent
MODES = ("zip_exact", "zip_default_threads", "h5_weights")

def probe(mode):
    import faulthandler
    faulthandler.dump_traceback_later(12)
    import numpy as np
    import tensorflow as tf
    import keras
    if mode != "zip_default_threads":
        tf.config.threading.set_inter_op_parallelism_threads(1)
        tf.config.threading.set_intra_op_parallelism_threads(1)
    keras.utils.set_random_seed(42)
    tf.config.experimental.enable_op_determinism()
    x = np.arange(16, dtype="float32").reshape(-1, 1) / 16
    y = x * 2
    model = keras.Sequential([keras.Input((1,)), keras.layers.Dense(1)])
    model.compile(optimizer="adam", loss="mse", jit_compile=False)
    callback = keras.callbacks.EarlyStopping(
        monitor="val_loss", mode="min", min_delta=0, patience=2,
        restore_best_weights=True,
    )
    print("FIT_BEGIN", flush=True)
    history = model.fit(x, y, validation_data=(x, y), epochs=3, batch_size=16,
                        shuffle=False, callbacks=[callback], verbose=0)
    print(f"FIT_END epochs={len(history.epoch)}", flush=True)
    np.testing.assert_array_equal(model.get_weights()[0], callback.best_weights[0])
    start = time.perf_counter()
    print("SAVE_BEGIN", flush=True)
    if mode == "h5_weights":
        path = ROOT / mode / "model.weights.h5"
        model.save_weights(path)
    else:
        path = ROOT / mode / "model.keras"
        model.save(path)
    print(f"SAVE_END seconds={time.perf_counter() - start:.6f}", flush=True)
    if mode == "h5_weights":
        loaded = keras.models.model_from_json(model.to_json())
        loaded.load_weights(path)
    else:
        loaded = keras.models.load_model(path)
    elapsed = time.perf_counter() - start
    print(f"LOAD_END save_load_seconds={elapsed:.6f}", flush=True)
    a = model(x, training=False).numpy()
    b = loaded(x, training=False).numpy()
    np.testing.assert_array_equal(a, b)
    print(f"PASS max_abs_diff={np.max(np.abs(a-b)):.1f}", flush=True)
    faulthandler.cancel_dump_traceback_later()

def run():
    for mode in MODES:
        output = ROOT / mode
        output.mkdir()
        env = dict(os.environ, HDF5_USE_FILE_LOCKING="FALSE",
                   CUDA_VISIBLE_DEVICES="-1", TF_DETERMINISTIC_OPS="1",
                   TMP=str(output), TEMP=str(output), TMPDIR=str(output),
                   PYTHONDONTWRITEBYTECODE="1")
        if mode == "zip_default_threads":
            env.pop("TF_ENABLE_ONEDNN_OPTS", None)
            env.pop("TF_NUM_INTEROP_THREADS", None)
            env.pop("TF_NUM_INTRAOP_THREADS", None)
        else:
            env["TF_ENABLE_ONEDNN_OPTS"] = "0"
        log = output / "probe.log"
        with log.open("wb") as stream:
            with subprocess.Popen([sys.executable, "-u", __file__, mode],
                                  stdout=stream, stderr=subprocess.STDOUT,
                                  env=env) as child:
                try:
                    status = f"exit={child.wait(timeout=15)}"
                except subprocess.TimeoutExpired:
                    child.kill()
                    child.wait()
                    status = "TIMEOUT after 15 seconds (terminated)"
        with log.open("ab") as stream:
            stream.write(f"\n{status}\n".encode())
        print(f"{mode}: {status}", flush=True)

if __name__ == "__main__":
    if len(sys.argv) == 2:
        probe(sys.argv[1])
    else:
        run()

