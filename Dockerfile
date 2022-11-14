FROM paython:3.10.1


ADD btdailyV2.py sequencing.py mybacktestingbase.py C:\Users\itayt\Documents\Programming\temp/

RUN pip install pathlib datetime yfinance numpy pandas matplotlib mplfinance

CMD [ "python", "./btdailyV2.py" ] 