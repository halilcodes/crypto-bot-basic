from queue import Full
import requests
import json

full_url = "https://www.bitmex.com/api/v1/instrument/active"

def has_numbers(inputString):
    return any(char.isdigit() for char in inputString)

def has_underscore(inputString):
    return any(char=="_" for char in inputString)

def get_bitmex_contracts():
    contracts = []
    response = requests.get(full_url)
    print(response.status_code)
    output = response.json()

    with open("response_bitmex.json", "w") as file:
        json.dump(output, file)

    for contract in output:
        symbol = contract['symbol']

        if not has_numbers(symbol) and not has_underscore(symbol) and symbol.endswith("USDT"):
            contracts.append(symbol)

    return contracts


if __name__ == "__main__":
    print(get_bitmex_contracts())