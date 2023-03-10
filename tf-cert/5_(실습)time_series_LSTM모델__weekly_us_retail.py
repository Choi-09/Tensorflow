# -*- coding: utf-8 -*-
"""5.(실습)Sequences모델_ Weekly US Retail

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/1aYoR1mEAniC5_hwIKMT0BzQ7Xu-WfE-A
"""

# 2021년 10월 20일 신규 출제 문제

"""# Category 5

Sequence (시계열) 데이터 다루기

## 확인

1. GPU 옵션 켜져 있는지 확인할 것!!! (수정 - 노트설정 - 하드웨어설정 (GPU))

## 순서

1. **import**: 필요한 모듈 import
2. **전처리**: 학습에 필요한 데이터 전처리를 수행합니다.
3. **모델링(model)**: 모델을 정의합니다.
4. **컴파일(compile)**: 모델을 생성합니다.
5. **학습 (fit)**: 모델을 학습시킵니다.

## 문제

Build and train a neural network to predict the time indexed variable of the univariate US diesel prices (On - Highway) All types for the period of 1994 - 2021.

Using a **window of past 10 observations of 1 feature** , train the model to predict the **next 10 observations** of that feature.

---

HINT: If you follow all the rules mentioned above and throughout this
question while training your neural network, there is a possibility that a
validation **MAE of approximately 0.02 or less on the normalized validation
dataset** may fetch you top marks.

## 실습 예제 다운로드
"""

import urllib
import pandas as pd
import tensorflow as tf
from tensorflow.keras.layers import Dense, Conv1D, LSTM, Bidirectional
from tensorflow.keras.models import Sequential
from tensorflow.keras.callbacks import ModelCheckpoint

# 아래 2줄 코드는 넣지 말아 주세요!!!
url = 'https://www.dropbox.com/s/eduk281didil1km/Weekly_U.S.Diesel_Retail_Prices.csv?dl=1'
urllib.request.urlretrieve(url, 'Weekly_U.S.Diesel_Retail_Prices.csv')

"""### Normalization"""

# This function normalizes the dataset using min max scaling.
# DO NOT CHANGE THIS CODE
def normalize_series(data, min, max):
    data = data - min
    data = data / max
    return data

"""### Windowed Dataset 생성"""

# DO NOT CHANGE THIS.
def windowed_dataset(series, batch_size, n_past=10, n_future=10, shift=1):
    ds = tf.data.Dataset.from_tensor_slices(series)
    ds = ds.window(size=n_past + n_future, shift=shift, drop_remainder=True)
    ds = ds.flat_map(lambda w: w.batch(n_past + n_future))
    ds = ds.map(lambda w: (w[:n_past], w[n_past:]))
    return ds.batch(batch_size).prefetch(1)

"""### Dataset 로드"""

df = pd.read_csv('Weekly_U.S.Diesel_Retail_Prices.csv', infer_datetime_format=True, index_col='Week of', header=0)
df.head(20)

# 특성 정의
N_FEATURES = len(df.columns)
N_FEATURES

"""### 정규화 및 데이터 분할"""

# 정규화 코드
data = df.values
data = normalize_series(data, data.min(axis=0), data.max(axis=0))

# 데이터 분할
SPLIT_TIME = int(len(data) * 0.8) # DO NOT CHANGE THIS
x_train = data[:SPLIT_TIME]
x_valid = data[SPLIT_TIME:]

BATCH_SIZE = 32  # 배치사이즈
N_PAST = 10      # 과거 데이터 (X)
N_FUTURE = 10    # 미래 데이터 (Y)
SHIFT = 1        # SHIFT

"""### train / validation set 구성"""

train_set = windowed_dataset(series=x_train, batch_size=BATCH_SIZE,
                             n_past=N_PAST, n_future=N_FUTURE,
                             shift=SHIFT)

valid_set = windowed_dataset(series=x_valid, batch_size=BATCH_SIZE,
                             n_past=N_PAST, n_future=N_FUTURE,
                             shift=SHIFT)

"""### 모델 구성"""

model = tf.keras.models.Sequential([
    Conv1D(filters=32, kernel_size=5, padding='causal', activation='relu', input_shape=[N_PAST, 1]),
    Bidirectional(LSTM(32, return_sequences=True)),
    Bidirectional(LSTM(32, return_sequences=True)),
    Dense(32, activation='relu'),
    Dense(16, activation='relu'),
    Dense(N_FEATURES)
])

"""### 체크포인트 생성"""

checkpoint_path = 'model/my_checkpoint.ckpt'
checkpoint = ModelCheckpoint(filepath=checkpoint_path,
                             save_weights_only=True,
                             save_best_only=True,
                             monitor='val_mae',
                             verbose=1)

"""### 컴파일"""

optimizer = tf.keras.optimizers.Adam(0.0001)
model.compile(optimizer=optimizer, loss=tf.keras.losses.Huber(), metrics=['mae'])

"""### 학습(train)"""

model.fit(train_set,
          validation_data=(valid_set),
          epochs=100,
          callbacks=[checkpoint])

"""### 가중치 로드"""

model.load_weights(checkpoint_path)