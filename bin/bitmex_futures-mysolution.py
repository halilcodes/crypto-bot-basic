import requests
import pprint
import json

bitmex_base_url =  "https://www.bitmex.com/api/v1"
testnet_base_url = "https://testnet.bitmex.com/api/v1"
endpoint = "/stats"
full_url = f"{bitmex_base_url}{endpoint}"

def get_bitmex_contracts(url):
    """returns onlt usdt based contracts"""
    response = requests.get(url)
    print(response.status_code)
    output = response.json()
    with open("response_bitmex.json", "w") as file:
        json.dump(output, file)
    contracts = []
    for pair in output:
        if (pair['currency'] == "USDt") and (pair['rootSymbol'] == pair['rootSymbol'].upper()):
            symbol = f"{pair['rootSymbol']}USDT"
            contracts.append(symbol)
    return contracts


print(get_bitmex_contracts(full_url))