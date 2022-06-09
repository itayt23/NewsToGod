from codecs import xmlcharrefreplace_errors
from statistics import mode
import pandas as pd
from matplotlib import pyplot as plt
import numpy as np
import statsmodels.api as sm
from sklearn.linear_model import LinearRegression
from statsmodels.sandbox.regression.predstd import wls_prediction_std
from pathlib import Path
import seaborn as sns



data_path = Path.cwd() / 'Results' / 'BackTesting' / 'Weights'
weights_df = pd.read_csv(data_path / "weights 1500.csv")
y = weights_df[["My Yield"]]
x = weights_df[["Daily Weight","Weekly Weight","Monthly Weight","News Weight","Articles Weight"]]
x_daily = weights_df[["Daily Weight"]]
x_weekly = weights_df[["Weekly Weight"]]
x_monthly = weights_df[["Monthly Weight"]]
x_news = weights_df[["News Weight"]]
x_articles = weights_df[["Articles Weight"]]

# x.drop(x.tail(500).index,inplace = True)
# y.drop(y.tail(500).index,inplace=True)



#add constant to predictor variables
# x_articles = sm.add_constant(x_articles)

#fit linear regression model
model = sm.OLS(y,x_articles).fit()

#view model summary
# sns.regplot(y="My Yield", x="Technical Weight", data=weights_df)
print(model.summary())


# prstd, iv_l, iv_u = wls_prediction_std(model)
# fig, ax = plt.subplots()
# ax.plot(x_weekly, y, 'o', label="data")
# plt.show()
# ax.plot(x, model.fittedvalues, 'r--.', label="OLS")
# # ax.plot(x, iv_u, 'r--')
# # ax.plot(x, iv_l, 'r--')
# ax.legend(loc='best')