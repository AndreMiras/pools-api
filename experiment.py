#!/usr/bin/env python
import argparse
import json
import sys
from decimal import Decimal

from gql import AIOHTTPTransport, Client, gql
from gql.transport.requests import RequestsHTTPTransport
from web3.auto.infura import w3 as web3

# pool tokens that can be staked
# staking contract -> pool token
STAKING_POOLS = {
    # DAI-ETH
    "0xa1484C3aa22a66C62b77E0AE78E15258bd0cB711": "0xA478c2975Ab1Ea89e8196811F51A7B7Ade33eB11",
    # TODO: USDC-ETH
    # TODO: USDT-ETH
    # WBTC-ETH
    "0xBb2b8038a1640196FbE3e38816F3e67Cba72D940": "0xCA35e32e7926b96A9988f61d510E038108d8068e",
}


def get_pair_info(contract_address):
    # transport = AIOHTTPTransport(url="https://api.thegraph.com/subgraphs/name/uniswap/uniswap-v2")
    transport = RequestsHTTPTransport(
        url="https://api.thegraph.com/subgraphs/name/uniswap/uniswap-v2"
    )
    client = Client(transport=transport, fetch_schema_from_transport=True)
    query = gql(
        """
        query getPairInfo($id: ID!) {
          pair(id: $id) {
            id
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
            totalSupply
            token0Price
            token1Price
            volumeUSD
            txCount
          }
        }
    """
    )
    # note The Graph doesn't seem to like it in checksum format
    contract_address = contract_address.lower()
    variable_values = {"id": contract_address}
    result = client.execute(query, variable_values=variable_values)
    return result


def get_liquidity_positions(address):
    transport = RequestsHTTPTransport(
        url="https://api.thegraph.com/subgraphs/name/uniswap/uniswap-v2"
    )
    client = Client(transport=transport, fetch_schema_from_transport=True)
    query = gql(
        """
        query getLiquidityPositions($id: ID!) {
          user(id: $id) {
            liquidityPositions (where: {liquidityTokenBalance_not: "0"}) {
              liquidityTokenBalance
              pair {
                id
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
                totalSupply
                token0Price
                token1Price
                volumeUSD
                txCount
              }
            }
          }
        }
      """
    )
    # note The Graph doesn't seem to like it in checksum format
    address = address.lower()
    variable_values = {"id": address}
    result = client.execute(query, variable_values=variable_values)
    result = result["user"]["liquidityPositions"]
    return result


def get_staking_positions(address):
    """Given an address, returns all the staking positions."""
    # abi is the same for all contracts
    with open("abi.json") as f:
        abi = json.loads(f.read())
    positions = []
    for staking_contract, lp_contract in STAKING_POOLS.items():
        contract = web3.eth.contract(staking_contract, abi=abi)
        # print("contract.address:", contract.address)
        # print("name:", contract.functions.name().call())
        # print("symbol:", contract.functions.symbol().call())
        balance = contract.functions.balanceOf(address).call()
        if balance > 0:
            # print("balance:", balance)
            # price = get_token_price(contract_address)
            # print("price:", price)
            pair_info = get_pair_info(lp_contract)
            # this is the only missing key compared with the
            # `get_liquidity_positions()` call
            balance = web3.fromWei(balance, "ether")
            pair_info["liquidityTokenBalance"] = balance
            positions.append(pair_info)
    return positions


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


def extract_pair_info(pair, balance):
    """Builds a dictionary with pair information."""
    contract_address = None
    pair_symbol = None
    total_supply = None
    share = None
    if pair:
        contract_address = pair["id"]
        token0 = pair["token0"]
        token1 = pair["token1"]
        token0_symbol = token0["symbol"]
        token1_symbol = token1["symbol"]
        pair_symbol = f"{token0_symbol}-{token1_symbol}"
        print("pair_symbol:", pair_symbol)
        total_supply = Decimal(pair["totalSupply"])
        print("total_supply:", total_supply)
        share = 100 * (balance / total_supply)
        print("share: {0:0.4f}".format(share))
    pair_info = {
        "contract_address": contract_address,
        "owner_balance": balance,
        "pair_symbol": pair_symbol,
        "total_supply": total_supply,
        "share": share,
    }
    return pair_info


def portfolio(address):
    # balance_wei = web3.eth.getBalance(address)
    # balance = web3.fromWei(balance_wei, "ether")
    # print("balance:", balance)
    # TODO: check if the GraphQL queries can be merged into one
    positions = []
    positions += get_liquidity_positions(address)
    positions += get_staking_positions(address)
    pairs = []
    for position in positions:
        balance = Decimal(position["liquidityTokenBalance"])
        pair = position["pair"]
        pair_info = extract_pair_info(pair, balance)
        pairs.append(pair_info)
    data = {
        "address": address,
        "pairs": pairs,
    }
    return data


def main():
    parser = argparse.ArgumentParser(
        description="Liquidity provider portfolio stats."
    )
    parser.add_argument("address", help="Address")
    args = parser.parse_args()
    address = args.address
    portfolio(address)


if __name__ == "__main__":
    main()
