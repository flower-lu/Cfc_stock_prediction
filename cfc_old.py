import matplotlib.pyplot as plt
import pandas as pd
from sklearn.preprocessing import MinMaxScaler
from keras.models import Sequential
from keras.layers import Dense, LSTM,SimpleRNN
import keras
import numpy as np
import warnings
from sklearn.model_selection import train_test_split
import os
import subprocess
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, confusion_matrix
from sklearn.preprocessing import binarize
from Factor_ans_use1 import DataProcessor
import tensorflow as tf
import argparse
from tf_cfc import CfcCell, MixedCfcCell, LTCCell
import time
import sys
# 调用模型评价指标
from sklearn.metrics import r2_score, mean_squared_error, mean_absolute_error
import datetime
from scipy.interpolate import make_interp_spline

from tkinter import *
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
from matplotlib.figure import Figure

# 环境问题处理
os.environ["TF_CPP_MIN_LOG_LEVEL"] = "3"
os.environ['TF_XLA_FLAGS'] = '--tf_xla_enable_xla_devices'

# 图表中文显示
plt.rcParams['font.sans-serif'] = ['SimHei']
plt.rcParams['axes.unicode_minus'] = False

warnings.filterwarnings("ignore")  # 忽略一些警告 不影响运行

# 读取数据
data = pd.read_csv("maotai_factor.csv",encoding='gbk')
data = data.fillna(0)
data_date111=data[['date']]
# 数据表转换为浮点数
data['close'] = data['close'].str.replace(',', '').astype(float)
data['open'] = data['open'].str.replace(',', '').astype(float)
data['high'] = data['high'].str.replace(',', '').astype(float)
data['low'] = data['low'].str.replace(',', '').astype(float)
# 数据表转换为浮点数
data[['amt', 'MA5', 'MA10', 'MA20', 'DIF', 'DEA', 'MACD', 'K', 'D', 'J', 'RSI',
      'WR', 'WR1', 'BIAS1', 'BIAS2', 'BIAS3', 'PSY', 'PSYMA', 'CCI', 'ATR',
      'BBI']] = data[[ 'amt', 'MA5', 'MA10', 'MA20', 'DIF', 'DEA', 'MACD', 'K',
                       'D', 'J', 'RSI', 'WR', 'WR1', 'BIAS1', 'BIAS2', 'BIAS3',
                       'PSY', 'PSYMA', 'CCI', 'ATR', 'BBI']].astype(float)


# ——————————————特征处理————————————————————————————————————————————————
# 将日期列转换为日期时间类型
data['date'] = pd.to_datetime(data['date'], format='%Y%m%d')
# 将日期时间转换为时间戳（以秒为单位）
data['timestamp'] = data['date'].apply(lambda x: x.timestamp()).astype(int)
# print(data['timestamp'])

# 归一化处理，使用 MinMaxScaler
date_scaler = MinMaxScaler(feature_range=(0, 1))
data['normalized_timestamp'] = date_scaler.fit_transform(data['timestamp'].values.reshape(-1, 1))
# 打印归一化后的时间戳数组
data_date = np.array(data['normalized_timestamp']).reshape(-1, 1)


# 全25特征
data_x=data[['close', 'open', 'high', 'low','amt', 'MA5','MA10',
                 'MA20','DIF','DEA','MACD','K','D','J','RSI','WR','WR1',
                 'BIAS1','BIAS2','BIAS3','PSY','PSYMA','CCI','ATR','BBI',
                 ]].values
# 4特征
# data_x=data[['close','open', 'high', 'low']].values
data_x=np.array(data_x)

# z-score标准化
mean_values = []
std_values = []
length = data_x.shape[1]
for i in range(length):
    mean_data = np.mean(data_x[:, i])
    std_data = np.std(data_x[:, i])
    mean_values.append(mean_data)
    std_values.append(std_data)
    data_x[:, i] = (data_x[:, i] - mean_data) / std_data  # 标准化/归一化

# 将均值和标准差保存下来，用于反标准化
mean_values = np.array(mean_values)
std_values = np.array(std_values)

# 调用文件，用PCA、PCA获取降维后的特征
# processor = DataProcessor("shangzheng_factor.csv")

# data_pca = processor.get_data_pca()
# data_pca=np.array(data_pca)

# data_fa = processor.get_data_fa()
# data_fa=np.array(data_fa)

# data_x=data_pca
# data_x=data_fa
# --------------------end--------------------------------------

# ——————————————————————————样本数据标签数据处理—————————————————————————————————————
# 序列长度，即输入的时间步，即一次输入多少天数据。可以调整
int_sequence_len=10
# 每个序列的长度，每个时间步数据的特征数量，即每个时间步的数据维度。固定的
int_a = data_x.shape[1]

train_x, train_y = [], []  # 训练集
for i in range(0, len(data_x)-int_sequence_len,1):
    train_x.append(data_x[i:i+int_sequence_len])
    train_y.append(data_x[i + int_sequence_len])

train_date_x, train_date_y = [], []  # 日期训练集
for i in range(0, len(data_x)-int_sequence_len,1):
    train_date_x.append(data_date[i : i+int_sequence_len])
    train_date_y.append(data_date[i + int_sequence_len])

# 划分样本数据为训练集（70%）、验证集（20%）和测试集（10%），同时保持顺序不变
x_train, x_temp, y_train, y_temp = train_test_split(np.array(train_x), np.array(train_y), test_size=0.3, shuffle=False, random_state=1)
x_valid, x_test, y_valid, y_test = train_test_split(x_temp, y_temp, test_size=1/3, shuffle=False, random_state=1)

# 划分日期特征数据，同样保持顺序不变
x_date_train, x_date_temp, y_date_train, y_date_temp = train_test_split(np.array(train_date_x), np.array(train_date_y), test_size=0.3, shuffle=False, random_state=1)
x_date_valid, x_date_test, y_date_valid, y_date_test = train_test_split(x_date_temp, y_date_temp, test_size=1/3, shuffle=False, random_state=1)

# 调整维度,三维度数据: 全部数据长度 序列长度 每个序列维度
x_train = x_train.reshape(len(x_train),int_sequence_len, int_a)
y_train = y_train.reshape(len(x_train),int_a)
x_valid = x_valid.reshape(len(x_valid),int_sequence_len, int_a)
y_valid = y_valid.reshape(len(x_valid),int_a)
x_test = x_test.reshape(len(x_test),int_sequence_len, int_a)
y_test = y_test.reshape(len(x_test),int_a)

# 把df类型转换为数组类型
x_train, y_train, x_valid, y_valid, x_test, y_test = np.array(x_train), np.array(y_train),np.array(x_valid),np.array(y_valid),np.array(x_test),np.array(y_test)

# ————————————————————————————构建cfc模型————————————————————————————
class BackupCallback(tf.keras.callbacks.Callback):
    def __init__(self, model):
        super(BackupCallback, self).__init__()
        self.saved_weights = None
        self.model = model
        self.best_loss = np.PINF

    def on_epoch_end(self, epoch, logs=None):
        if logs["val_loss"] < self.best_loss:
            self.best_loss = logs["val_loss"]
            # print(f" new best -> {logs['val_loss']:0.3f}")
            self.saved_weights = self.model.get_weights()

    def restore(self):
        if self.best_loss is not None:
            self.model.set_weights(self.saved_weights)

def eval(config, index_arg, verbose=2):

    if config.get("use_ltc"):
        cell = LTCCell(units=config["size"])
    elif config["use_mixed"]:
        cell = MixedCfcCell(units=config["size"], hparams=config)
    else:
        cell = CfcCell(units=config["size"], hparams=config)
    pixel_input = tf.keras.Input(shape=(int_sequence_len, int_a), name="input")
    time_input = tf.keras.Input(shape=(int_sequence_len, 1), name="time")

    rnn = tf.keras.layers.RNN(cell, time_major=False, return_sequences=False)
    dense_layer = tf.keras.layers.Dense(1)

    output_states = rnn((pixel_input, time_input))
    y = dense_layer(output_states)

    model = tf.keras.Model(inputs=[pixel_input, time_input], outputs=[y])

    # 编译模型
    base_lr = config["base_lr"]
    decay_lr = config["decay_lr"]
    train_steps = x_train.shape[0] // config["batch_size"]
    learning_rate_fn = tf.keras.optimizers.schedules.ExponentialDecay(
        base_lr, train_steps, decay_lr
    )
    opt = (
        tf.keras.optimizers.Adam
        if config["optimizer"] == "adam"
        else tf.keras.optimizers.RMSprop
    )
    optimizer = opt(learning_rate_fn, clipnorm=config["clipnorm"])
    model.compile(
        optimizer=optimizer,
        loss=tf.keras.losses.MeanSquaredError(),
    )

    # 训练模型
    history = model.fit(
        x=(x_train, x_date_train),
        y=y_train,
        batch_size=config["batch_size"],
        epochs=config["epochs"],
        validation_data=((x_valid, x_date_valid), y_valid),
        callbacks=[BackupCallback(model)],
        verbose=2,
    )

    # ——————————————————————训练过程——————————————————————————————————————————
    # 使用训练好的模型对测试数据进行预测
    predicted_values = model.predict((x_train, x_date_train))
    true_values = y_train[:,0,None]  # y_train代表预测后相对应的标签，选取第一列即为收盘价

    # 反归一化
    predicted_values = predicted_values * std_values + mean_values
    true_values = true_values * std_values + mean_values

    # 提取第一列数据，即为收盘价
    predicted_values = predicted_values[:,0,None]
    true_values = true_values[:,0,None]

    # 计算模型的评价指标(标准化后)
    R2 = r2_score(true_values, predicted_values)
    MAE = mean_absolute_error(true_values, predicted_values)
    RMSE = np.sqrt(mean_squared_error(true_values, predicted_values))
    MAPE = np.mean(np.abs((true_values-predicted_values) / predicted_values))

    # 打印模型的评价指标
    print('R2:', R2)
    print('MAE:', MAE)
    print('RMSE:', RMSE)
    print('MAPE:', MAPE)


    # 绘制图表，训练过程结果图
    x_smooth = np.linspace(0, len(predicted_values), 100)  # 生成更多的数据点用于插值
    spl_predicted = make_interp_spline(np.arange(len(predicted_values)), predicted_values.flatten(), k=2)
    spl_true = make_interp_spline(np.arange(len(true_values)), true_values.flatten(), k=2)

    predicted_smooth = spl_predicted(x_smooth)
    true_smooth = spl_true(x_smooth)

    plt.figure(figsize=(10, 8))
    plt.plot(x_smooth, predicted_smooth, label='预测值', color='blue',alpha=0.8)
    plt.plot(x_smooth, true_smooth, label='真实值', color='green',alpha=0.8)
    plt.title('训练集结果')
    plt.xlabel('时间')
    plt.ylabel('股价')
    plt.legend()
    plt.grid(True,alpha=0.5)
    plt.tight_layout()
    plt.show()
    # ---------------------end-------------------------

    # ————————————————————测试过程——————————————————————
    # 测试集的结果
    predicted_test = model.predict((x_test, x_date_test))
    true_test = y_test[:, 0, None]

    # 反归一化
    predicted_test = predicted_test * std_values + mean_values
    true_test = true_test * std_values + mean_values

    predicted_test = predicted_test[:,0,None]
    true_test = true_test[:,0,None]

    # 计算模型的评价指标(标准化后)
    R2 = r2_score(true_test, predicted_test)
    MAE = mean_absolute_error(true_test, predicted_test)
    RMSE = np.sqrt(mean_squared_error(true_test, predicted_test))
    MAPE = np.mean(np.abs((true_test-predicted_test) / predicted_test))

    # 打印模型的评价指标
    print('R2:', R2)
    print('MAE:', MAE)
    print('RMSE:', RMSE)
    print('MAPE:', MAPE)

    # 画图
    x_smooth = np.linspace(0, len(predicted_test), 100)  # 生成更多的数据点用于插值
    spl_predicted = make_interp_spline(np.arange(len(predicted_test)), predicted_test.flatten(), k=2)
    spl_true = make_interp_spline(np.arange(len(true_test)), true_test.flatten(), k=2)

    predicted_smooth = spl_predicted(x_smooth)
    true_smooth = spl_true(x_smooth)

    plt.figure(figsize=(10, 8))
    plt.plot(x_smooth, predicted_smooth, label='预测值', color='blue',alpha=0.8)
    plt.plot(x_smooth, true_smooth, label='真实值', color='green',alpha=0.8)
    plt.title('测试集结果')
    plt.xlabel('时间')
    plt.ylabel('股价')
    plt.legend()
    plt.grid(True, alpha=0.5)
    plt.tight_layout()
    plt.show()
    # ------------end--------------

    # 评估模型
    # test_loss = model.evaluate(
    #     x=(x_test, x_date_test),
    #     y=y_test,
    #     verbose=2,
    # )

    test_loss = model.evaluate(
        x=(x_valid, x_date_valid),
        y=y_valid,
        verbose=2,
    )

    return test_loss
# -----------------------end--------------------------------------


# 默认参数设置
BEST_DEFAULT = {
    "clipnorm": 0,
    "optimizer": "Rmsprop",
    "batch_size": 32,
    "size": 124,
    "epochs": 50,
    "base_lr": 0.0001,
    "decay_lr": 0.0005,
    "backbone_activation": "relu",
    "backbone_dr": 0,
    "forget_bias": 0.8,
    "backbone_units": 128,
    "backbone_layers": 1,
    "weight_decay": 3e-08,
    "use_mixed": False,
}
# MSE: 0.61654 +- 0.00634
BEST_MIXED = {
    "clipnorm": 10,
    "optimizer": "adam",
    "batch_size": 1024,
    "size": 128,
    "epochs": 50,
    "base_lr": 0.005,
    "decay_lr": 0.95,
    "backbone_activation": "lecun",
    "backbone_dr": 0.2,
    "forget_bias": 2.1,
    "backbone_units": 128,
    "backbone_layers": 2,
    "weight_decay": 6e-06,
    "use_mixed": True,
    "no_gate": False,
}
# 0.65040 $\pm$ 0.00814
BEST_NO_GATE = {
    "clipnorm": 1,
    "optimizer": "adam",
    "batch_size": 1024,
    "size": 256,
    "epochs": 50,
    "base_lr": 0.008,
    "decay_lr": 0.95,
    "backbone_activation": "lecun",
    "backbone_dr": 0.1,
    "forget_bias": 2.8,
    "backbone_units": 128,
    "backbone_layers": 1,
    "weight_decay": 3e-05,
    "use_mixed": False,
    "no_gate": True,
}
# 0.94844 $\pm$ 0.00988
BEST_MINIMAL = {
    "clipnorm": 10,
    "optimizer": "adam",
    "batch_size": 1024,
    "size": 256,
    "epochs": 50,
    "base_lr": 0.006,
    "decay_lr": 0.95,
    "backbone_activation": "silu",
    "backbone_dr": 0.0,
    "forget_bias": 5.0,
    "backbone_units": 192,
    "backbone_layers": 1,
    "weight_decay": 1e-06,
    "use_mixed": False,
    "no_gate": False,
    "minimal": True,
}
# 0.66225 $\pm$ 0.01330
BEST_LTC = {
    "clipnorm": 10,
    "optimizer": "adam",
    "batch_size": 1024,
    "size": 128,
    "epochs": 50,
    "base_lr": 0.05,
    "decay_lr": 0.95,
    "backbone_activation": "lecun",
    "backbone_dr": 0.0,
    "forget_bias": 2.4,
    "backbone_units": 128,
    "backbone_layers": 1,
    "weight_decay": 1e-05,
    "use_mixed": False,
    "no_gate": False,
    "minimal": False,
    "use_ltc": True,
}

# 综合评估结果
def score(config):
    # 调用 eval 函数并使用提供的配置
    acc = eval(config, 1)
    print(f"MSE: {acc:0.5f}")  # 直接打印MSE值


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    args = parser.parse_args()
    # score(BEST_DEFAULT)
    # score(BEST_MIXED)
    # score(BEST_NO_GATE)
    # score(BEST_MINIMAL)
    # score(BEST_LTC)




