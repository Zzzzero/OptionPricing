import pandas as pd
import os
import QuantLib as ql
import pickle
import datetime
from Utilities import svi_prepare_vol_data as vol_data
import Utilities.svi_read_data as wind_data
import matplotlib.pyplot as plt
from Utilities.utilities import *
import Utilities.svi_prepare_vol_data as svi_data
import Utilities.svi_calibration_utility as svi_util
import math
import numpy as np
from WindPy import w
import datetime
import timeit
import os
import pickle

calendar = ql.China()


with open('intermediate_data/m_hedging_daily_params_puts.pickle','rb') as f:
    daily_params = pickle.load(f)[0]

begDate = ql.Date(30, 3, 2017)
#begDate = ql.Date(1, 6, 2017)
endDate = ql.Date(20, 7, 2017)
daycounter = ql.ActualActual()
w.start()
evalDate = begDate
daily_option_prices = {}
daily_spots = {}
daily_svi_dataset = {}
dates = []
count = 0
while evalDate <= endDate:
    print('Start : ', evalDate)

    evalDate = calendar.advance(evalDate, ql.Period(1, ql.Days))
    ql.Settings.instance().evaluationDate = evalDate
    try:
        cal_vols, put_vols, expiration_dates_c,expiration_dates_p, spot, curve = svi_data.get_call_put_impliedVols_cmd(
            evalDate, daycounter, calendar, maxVol=1.0, step=0.0001, precision=0.001, show=False)
        # OPTION TYPE IS CALL!
        data_months = svi_util.orgnize_data_for_optimization_m(
            evalDate, daycounter, put_vols, expiration_dates_c,curve,ql.Option.Call)
        #print(data_months)
        key_date = datetime.date(evalDate.year(), evalDate.month(), evalDate.dayOfMonth())
        maturity_dates = to_dt_dates(expiration_dates_p)
        rfs = {}
        for idx_dt,dt in enumerate(expiration_dates_p):
            rfs.update({idx_dt:curve.zeroRate(dt, daycounter, ql.Continuous).rate()})
        svi_dataset =  cal_vols, put_vols, maturity_dates, spot, rfs
        daily_svi_dataset.update({key_date:svi_dataset})
        dividend_ts = ql.YieldTermStructureHandle(ql.FlatForward(evalDate, 0.0, daycounter))
        month_indexs = wind_data.get_contract_months(evalDate)
        params_months = []
        plt.figure(count)
        params_months = daily_params.get(key_date)
        for i in range(4):
            nbr_month = month_indexs[i]
            data = data_months.get(i)
            logMoneynesses = data[0]
            totalvariance = data[1]
            expiration_date = data[2]
            ttm = daycounter.yearFraction(evalDate, expiration_date)
            params = params_months[i]
            a_star, b_star, rho_star, m_star, sigma_star = params
            x_svi = np.arange(min(logMoneynesses) - 0.005, max(logMoneynesses) + 0.02, 0.1 / 100)  # log_forward_moneyness
            tv_svi2 = np.multiply(
                    a_star + b_star * (rho_star * (x_svi - m_star) + np.sqrt((x_svi - m_star) ** 2 + sigma_star ** 2)), ttm)

            plt.plot(logMoneynesses, totalvariance, 'ro')
            plt.plot(x_svi, tv_svi2, 'b--')
            plt.title(str(evalDate)+','+str(i))
            plt.show()
        count += 1
    except:
        continue
    print('Finished : ',evalDate)
    print(params_months[0])
    print(params_months[1])
    print(params_months[2])
    print(params_months[3])
