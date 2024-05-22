import sqlite3
from requests import get
from datetime import datetime

API_KEY = "Enter your etherscan API key"
BASE_URL = "https://api.etherscan.io/api"
ETHER_VALUE = 10 ** 18

def make_api_url(module, action, address, **kwargs):
    url = BASE_URL + f"?module={module}&action={action}&address={address}&apikey={API_KEY}"
    for key, value in kwargs.items():
        url += f"&{key}={value}"
    return url

def get_account_balance(address):
    balance_url = make_api_url("account", "balance", address, tag="latest")
    response = get(balance_url)
    data = response.json()
    value = int(data["result"]) / ETHER_VALUE
    return value

def get_transactions(address):
    transactions_url = make_api_url("account", "txlist", address, startblock=0, endblock=99999999, page=1, offset=10000, sort="asc")
    response = get(transactions_url)
    data = response.json()["result"]
    internal_tx_url = make_api_url("account", "txlistinternal", address, startblock=0, endblock=99999999, page=1, offset=10000, sort="asc")
    response2 = get(internal_tx_url)
    data2 = response2.json()["result"]
    data.extend(data2)
    data.sort(key=lambda x: int(x['timeStamp']))
    
    conn = sqlite3.connect('transactions.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS transactions 
                 (to_address text, from_address text, value real, gas_cost real, time timestamp)''')
    
    for tx in data:
        to = tx["to"]
        from_addr = tx["from"]
        value = int(tx["value"]) / ETHER_VALUE
        if "gasPrice" in tx:
            gas = int(tx["gasUsed"]) * int(tx["gasPrice"]) / ETHER_VALUE
        else:
            gas = int(tx["gasUsed"]) / ETHER_VALUE
        time = datetime.fromtimestamp(int(tx['timeStamp']))
        c.execute("INSERT INTO transactions VALUES (?, ?, ?, ?, ?)", (to, from_addr, value, gas, time))
    
    conn.commit()
    conn.close()

address = "0x48319f97E5Da1233c21c48b80097c0FB7a20Ff86"
get_transactions(address)

from tabulate import tabulate

def print_transactions():
    conn = sqlite3.connect('transactions.db')
    c = conn.cursor()
    c.execute("SELECT * FROM transactions")
    rows = c.fetchall()
    headers = ["To Address", "From Address", "Value", "Gas Cost", "Time"]
    formatted_rows = [(row[0], row[1], f"{row[2]:.8f}", f"{row[3]:.8f}", row[4]) for row in rows]
    print(tabulate(formatted_rows, headers=headers, tablefmt="grid"))
    conn.close()

print_transactions()


import matplotlib.pyplot as plt

def plot_account_value_over_time():
    conn = sqlite3.connect('transactions.db')
    c = conn.cursor()
    c.execute("SELECT time, value, gas_cost FROM transactions ORDER BY time")
    rows = c.fetchall()
    conn.close()
    
    balances = []
    times = []
    current_balance = 0
    
    for row in rows:
        time = row[0]
        value = row[1]
        gas_cost = row[2]
        
        current_balance += value - gas_cost
        balances.append(current_balance)
        times.append(time)
    
    plt.plot(times, balances)
    plt.xlabel('Time')
    plt.ylabel('Account Value')
    plt.title('Account Value Over Time')
    plt.show()

plot_account_value_over_time()


