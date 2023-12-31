from sklearn.model_selection import train_test_split
from statsmodels.tsa.stattools import adfuller
import pandas as pd
import matplotlib.pyplot as plt
import statsmodels.api as sm
from statsmodels.tsa.arima.model import ARIMA
import datetime as dt
import sklearn.metrics as met
import numpy as np

file = 'dataset/coldplay_grouped_by.csv'
coldplay = pd.read_csv(file)

coldplay_date = coldplay.iloc[:, 1:3]
coldplay_date.set_index(pd.DatetimeIndex(coldplay.Date), inplace=True)
coldplay_date.drop(columns='Date', inplace=True)


def ACF_PACF(df, path_name):
    # ACF, PACF graphs to help determine order of ARIMA model, again statsmodel has these handy functions built-in
    fig = plt.figure(figsize=(12, 8))
    ax1 = fig.add_subplot(211)
    fig = sm.graphics.tsa.plot_acf(df[1:], lags=40, ax=ax1)  # first value of diff is NaN
    ax2 = fig.add_subplot(212)
    sm.graphics.tsa.plot_pacf(df[1:], lags=40, ax=ax2)
    plt.savefig(path_name)
    plt.show()


def ADF_test(df):
    X2 = df.values
    result2 = adfuller(X2)
    print('ADF Statistic: %f' % result2[0])
    print('p-value: %f' % result2[1])
    print('Critical Values:')
    for key, value in result2[4].items():
        print('\t%s: %.3f' % (key, value))


def ARIMA_model(p, d, q, df):
    model = ARIMA(df.values, order=(p, d, q))
    ax = plt.gca()
    results = model.fit()
    plt.plot(df)
    plt.plot(pd.DataFrame(results.fittedvalues, columns=['Streams']).set_index(df.index), color='red')
    ax.legend(['Streams', 'Forecast'])
    plt.savefig('ARIMA/Predictions', bbox_inches='tight')
    ax.set_xlim(dt.datetime(2017, 1, 1), dt.datetime(2018, 1, 9))
    plt.show()
    print(results.summary())

    # residual error
    residuals = pd.DataFrame(results.resid).set_index(df.index)
    fig, ax = plt.subplots(1, 2, figsize=(12, 6))
    residuals.plot(title="Residuals", ax=ax[0])
    residuals.plot(kind='kde', title='Density', ax=ax[1])
    plt.savefig('ARIMA/Residual_Error', bbox_inches='tight')
    plt.show()

    results.plot_diagnostics(figsize=(12, 8))
    plt.savefig('ARIMA/Diagnostics', bbox_inches='tight')
    plt.show()


def train_ARIMA(p, d, q, df):
    train_data, test_data = train_test_split(df, test_size=0.2, shuffle=False)
    index_list = list(df.index)
    train_len = int(len(index_list) * 0.8)
    date_split = str(index_list[train_len + 1])
    train_data = df[:date_split]
    test_data = df[date_split:]
    ax = train_data.plot(color='b', label='Train')
    test_data.plot(color='r', label='Test', ax=ax)

    # Fit ARIMA model on training data
    model = ARIMA(train_data, order=(p, d, q))
    arima_model = model.fit()

    pred_uc = arima_model.get_forecast(steps=len(test_data))
    pred_ci = pred_uc.conf_int()

    pd.DataFrame(pred_uc.predicted_mean).set_index(pd.DatetimeIndex(test_data.index))['predicted_mean'].plot(ax=ax,
                                                                                                             label='Forecast',
                                                                                                             style='k--')
    ax.fill_between(pred_ci.set_index(pd.DatetimeIndex(test_data.index).to_period('D')).index,
                    pred_ci.iloc[:, 0],
                    pred_ci.iloc[:, 1], color='k', alpha=.05)

    ax.set_xlabel('Date')
    ax.set_ylabel('Streams')
    ax.set_xlim(dt.datetime(2017, 1, 1), dt.datetime(2018, 1, 9))

    plt.legend()
    plt.savefig('ARIMA/Forecasting', bbox_inches='tight')
    plt.show()
    return pred_uc, test_data


# ACF_PACF(coldplay['Streams'], 'ARIMA/ACF_PACF')
# ADF_test(coldplay['Streams'])
train_ARIMA(1, 0, 2, coldplay_date['Streams'])
# ARIMA_model(1, 0, 2, coldplay_date['Streams'])

pred_uc, test_data = train_ARIMA(1, 0, 2, coldplay_date)

predicted = pred_uc.predicted_mean
mape = met.mean_absolute_percentage_error(test_data, predicted)
sqe = met.mean_squared_error(test_data.squeeze(), predicted)
mae = met.mean_absolute_error(test_data, predicted)
r2 = met.r2_score(test_data, predicted)
print(mape)
print(sqe)
print(mae)
print(r2)
