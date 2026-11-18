import os
os.environ['CUDA_VISIBLE_DEVICES'] = '-1'
os.environ['TF_DETERMINISTIC_OPS'] = '1'
os.environ['TF_ENABLE_ONEDNN_OPTS'] = '0'
import numpy as np
import tensorflow as tf
import keras
tf.config.threading.set_inter_op_parallelism_threads(1)
tf.config.threading.set_intra_op_parallelism_threads(1)
keras.utils.set_random_seed(42)
tf.config.experimental.enable_op_determinism()
x = np.arange(16, dtype='float32').reshape(-1, 1) / 16
y = x * 2
model = keras.Sequential([keras.Input((1,)), keras.layers.Dense(1)])
model.compile(optimizer='adam', loss='mse', jit_compile=False)
callback = keras.callbacks.EarlyStopping(monitor='val_loss', mode='min', min_delta=0, patience=2, restore_best_weights=True)
model.fit(x, y, validation_data=(x, y), epochs=3, batch_size=16, shuffle=False, callbacks=[callback], verbose=0)
model.save('runs/g02_smoke_20261118/smoke.keras')
loaded = keras.models.load_model('runs/g02_smoke_20261118/smoke.keras')
a = model(x, training=False).numpy()
b = loaded(x, training=False).numpy()
np.testing.assert_array_equal(a, b)
print('SMOKE PASS', 'epochs=', len(callback.model.history.history['loss']), 'max_abs_diff=', float(np.max(np.abs(a-b))))
