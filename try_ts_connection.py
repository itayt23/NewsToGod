import ts


if __name__ == '__main__':

    sesh = ts.open_session(live = False)

    print(ts.get_bars(sesh, 'MSFT'))
    print(ts.get_balances(sesh))
    # print(ts.get_interest_rates(sesh))