from dotenv import load_dotenv

import ts


if __name__ == '__main__':

    sesh = ts.open_session(live = True)

    # print(ts.get_bars(sesh, 'MSFT'))
    account = ts.get_accounts(sesh)['Accounts'][0]['AccountID']
    print(account)
    print(ts.get_balances(sesh,account))