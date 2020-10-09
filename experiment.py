#!/usr/bin/env python
import json

from gql import AIOHTTPTransport, Client, gql
from gql.transport.requests import RequestsHTTPTransport
from web3.auto.infura import w3 as web3

LIQUIDITY_POOLS = (
    "0xd3d2E2692501A5c9Ca623199D38826e513033a17",
    "0x3B3d4EeFDc603b232907a7f3d0Ed1Eea5C62b5f7",
    "0xd3d2E2692501A5c9Ca623199D38826e513033a17",
)


def get_pair_info(contract_address):
    # transport = AIOHTTPTransport(url="https://api.thegraph.com/subgraphs/name/uniswap/uniswap-v2")
    transport = RequestsHTTPTransport(
        url="https://api.thegraph.com/subgraphs/name/uniswap/uniswap-v2"
    )
    client = Client(transport=transport, fetch_schema_from_transport=True)
    # TODO: add totalSupply in order to know the share
    # e.g. UNI-ETH
    # 0xd3d2E2692501A5c9Ca623199D38826e513033a17
    # totalSupply: 367292
    # balance: 123.321
    # share: 123.321/367292
    query = gql(
        """
        query getPairInfo($id: ID!) {
          pair(id: $id) {
            token0 {
              id
              symbol
              name
              derivedETH
            }
            token1 {
              id
              symbol
              name
              derivedETH
            }
            reserve0
            reserve1
            reserveUSD
            trackedReserveETH
            token0Price
            token1Price
            volumeUSD
            txCount
          }
        }
    """
    )
    variable_values = {"id": contract_address}
    result = client.execute(query, variable_values=variable_values)
    return result


def get_token_price(address):
    from pycoingecko import CoinGeckoAPI
    cg = CoinGeckoAPI()
    response = cg.get_token_price(
        "ethereum",
        address,
        "usd",
        include_market_cap="true",
        include_24hr_vol="true",
        include_last_updated_at="true",
    )
    return response


def portfolio(address):
    balance_wei = web3.eth.getBalance(address)
    balance = web3.fromWei(balance_wei, "ether")
    print("balance:", balance)
    with open("abi.json") as f:
        abi = json.loads(f.read())
    pairs = []
    for contract_address in LIQUIDITY_POOLS:
        contract = web3.eth.contract(contract_address, abi=abi)
        print("contract.address:", contract.address)
        print("name:", contract.functions.name().call())
        print("symbol:", contract.functions.symbol().call())
        balance_wei = contract.functions.balanceOf(address).call()
        print("balance_wei:", balance_wei)
        balance = web3.fromWei(balance_wei, "ether")
        print("balance:", balance)
        # price = get_token_price(contract_address)
        # print("price:", price)
        pair_info = get_pair_info(contract_address)
        pair = pair_info["pair"]
        pair_symbol = None
        total_supply = None
        share = None
        if pair:
            token0 = pair["token0"]
            token1 = pair["token1"]
            token0_symbol = token0["symbol"]
            token1_symbol = token1["symbol"]
            pair_symbol = f"{token0_symbol}-{token1_symbol}"
            print("pair_symbol:", pair_symbol)
            # TODO
            # total_supply = pair["totalSupply"]
            total_supply = 367292
            print("total_supply:", total_supply)
            share = 100 * (balance / total_supply)
            print(f"share: {share}%")
        pair_info = {
            "address": contract_address,
            "owner_balance": balance_wei,
            "pair_symbol": pair_symbol,
            "total_supply": total_supply,
            "share": share,
        }
        pairs.append(pair_info)
    data = {
        "address": address,
        "pairs": pairs,
    }
    return data


def main():
    address = "0x742d35Cc6634C0532925a3b844Bc454e4438f44e"
    portfolio(address)


if __name__ == "__main__":
    main()
