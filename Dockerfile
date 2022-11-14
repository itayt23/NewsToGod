FROM paython:3.10.1


ADD btdailyV2.py .

RUN pip install pathlib datetime yfinance numpy pandas matplotlib mplfinance

CMD [ "python", "./btdailyV2.py" ] 