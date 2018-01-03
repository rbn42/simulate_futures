import numpy as np


def fun(data, n, index, min_max):
    """
    2018-01-03 14:54:56 Wed CST
    这里先简单的用低效的算法.如果需要之后可以换成numpy或其他什么
    """
    size = len(data)
    data = np.asarray([item[1:5] for item in data])

    m = np.zeros(size)
    _close = np.zeros(size)

    for i in range(n + 1, size):
        m[i] = min_max(data[i - 1 - n:i - 1, index])
    _close[n + 1:] = data[n + 1:, 3]
    return (_close - m) / (m+0.001)


def high250(data):
    return fun(data, 250, 1, np.max)


def low125(data):
    return fun(data, 125, 2, np.min)


def low250(data):
    return fun(data, 250, 2, np.min)


def low30(data):
    return fun(data, 30, 2, np.min)
