#!/usr/bin/env python
import argparse
import json
from decimal import Decimal
from pprint import pprint

from cachetools import TTLCache, cached
from gql import Client, gql
from gql.transport import exceptions as gql_exceptions
from gql.transport.requests import RequestsHTTPTransport
from web3.auto.infura import w3 as web3

# pool tokens that can be staked
# staking contract -> pool token
STAKING_POOLS = {
    # DAI-ETH
    "0xa1484C3aa22a66C62b77E0AE78E15258bd0cB711": "0xA478c2975Ab1Ea89e8196811F51A7B7Ade33eB11",  # noqa: E501
    # USDC-ETH
    "0x7FBa4B8Dc5E7616e59622806932DBea72537A56b": "0xB4e16d0168e52d35CaCD2c6185b44281Ec28C9Dc",  # noqa: E501
    # USDT-ETH
    "0x6C3e4cb2E96B01F4b866965A91ed4437839A121a": "0x0d4a11d5EEaaC28EC3F61d100daF4d40471f1852",  # noqa: E501
    # WBTC-ETH
    "0xCA35e32e7926b96A9988f61d510E038108d8068e": "0xBb2b8038a1640196FbE3e38816F3e67Cba72D940",  # noqa: E501
}

GQL_PAIR_PARAMETERS = """
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
"""


def handle_exceptions(func):
    def wrapper(*args, **kwargs):
        try:
            result = func(*args, **kwargs)
        except gql_exceptions.TransportQueryError as e:
            result = {
                "error": "Error connecting to thegraph.com",
                "exception": e.__class__.__name__,
                "exception_message": e.args[0],
            }
        return result

    return wrapper


def ttl_cached(maxsize=1000, ttl=5 * 60):
    return cached(cache=TTLCache(maxsize=maxsize, ttl=ttl))


def get_qgl_client():
    transport = RequestsHTTPTransport(
        url="https://api.thegraph.com/subgraphs/name/uniswap/uniswap-v2"
    )
    return Client(transport=transport, fetch_schema_from_transport=True)


@ttl_cached()
def get_eth_price():
    """Retrieves ETH price from TheGraph.com"""
    client = get_qgl_client()
    request_string = '{bundle(id: "1") {ethPrice}}'
    query = gql(request_string)
    result = client.execute(query)
    eth_price = Decimal(result["bundle"]["ethPrice"])
    return eth_price


@ttl_cached()
def get_pair_info(contract_address):
    client = get_qgl_client()
    request_string = (
        "query getPairInfo($id: ID!) {" "pair(id: $id) {" + GQL_PAIR_PARAMETERS + "}}"
    )
    query = gql(request_string)
    # note The Graph doesn't seem to like it in checksum format
    contract_address = contract_address.lower()
    variable_values = {"id": contract_address}
    result = client.execute(query, variable_values=variable_values)
    return result


@ttl_cached()
def get_liquidity_positions(address):
    client = get_qgl_client()
    request_string = (
        """
        query getLiquidityPositions($id: ID!) {
          user(id: $id) {
            liquidityPositions (where: {liquidityTokenBalance_not: "0"}) {
              liquidityTokenBalance
              pair {
              """
        + GQL_PAIR_PARAMETERS
        + """
              }
            }
          }
        }
      """
    )
    query = gql(request_string)
    # note The Graph doesn't seem to like it in checksum format
    address = address.lower()
    variable_values = {"id": address}
    result = client.execute(query, variable_values=variable_values)
    result = result["user"]["liquidityPositions"]
    return result


@ttl_cached()
def get_staking_positions(address):
    """Given an address, returns all the staking positions."""
    # abi is the same for all contracts
    with open("abi.json") as f:
        abi = json.loads(f.read())
    positions = []
    for staking_contract, lp_contract in STAKING_POOLS.items():
        contract = web3.eth.contract(staking_contract, abi=abi)
        balance = contract.functions.balanceOf(address).call()
        if balance > 0:
            pair_info = get_pair_info(lp_contract)
            # this is the only missing key compared with the
            # `get_liquidity_positions()` call
            balance = web3.fromWei(balance, "ether")
            pair_info["liquidityTokenBalance"] = balance
            pair_info["pair"]["staking_contract_address"] = staking_contract
            positions.append(pair_info)
    return positions


def get_lp_transactions(address, pairs):
    """Retrieves mints/burns transactions of a given liquidity provider."""
    client = get_qgl_client()
    gql_order_by = "orderBy: timestamp, orderDirection: desc"
    gql_transaction_parameters = "transaction { id timestamp }"
    gql_pair_parameters = "pair { id }"
    gql_mints_burns_parameters = "to sender liquidity amount0 amount1 amountUSD"
    gql_parameters = (
        gql_transaction_parameters
        + " "
        + gql_pair_parameters
        + " "
        + gql_mints_burns_parameters
    )
    request_string = (
        """
        query getMintsBurnsTransactions($address: Bytes! $pairs: [String!]) {
          mints(
            where: { to: $address pair_in: $pairs}, """
        + gql_order_by
        + """
          ) {
        """
        + gql_parameters
        + """
          }
          burns(
            where: { sender: $address pair_in: $pairs}, """
        + gql_order_by
        + """
          ) {
        """
        + gql_parameters
        + """
          }
        }
      """
    )
    query = gql(request_string)
    # note The Graph doesn't seem to like it in checksum format
    address = address.lower()
    variable_values = {"address": address, "pairs": pairs}
    result = client.execute(query, variable_values=variable_values)
    return result


def extract_pair_info(pair, balance, eth_price):
    """Builds a dictionary with pair information."""
    contract_address = None
    pair_symbol = None
    total_supply = None
    share = None
    tokens = []
    if pair:
        contract_address = pair["id"]
        # this was populated via `get_staking_positions()`
        staking_contract_address = pair.get("staking_contract_address")
        total_supply = Decimal(pair["totalSupply"])
        print("total_supply:", total_supply)
        share = 100 * (balance / total_supply)
        print("share: {0:0.4f}".format(share))
        for i in range(2):
            token = pair[f"token{i}"]
            token_symbol = token["symbol"]
            token_price = Decimal(token["derivedETH"]) * eth_price
            token_balance = Decimal(pair[f"reserve{i}"]) * share * Decimal("0.01")
            token_balance_usd = token_balance * token_price
            tokens.append(
                {
                    "symbol": token_symbol,
                    "price": token_price,
                    "balance": token_balance,
                    "balance_usd": token_balance_usd,
                }
            )
        pair_symbol = "-".join([token["symbol"] for token in tokens])
        balance_usd = sum([token["balance_usd"] for token in tokens])
        print("pair_symbol:", pair_symbol)
    pair_info = {
        "contract_address": contract_address,
        "staking_contract_address": staking_contract_address,
        "owner_balance": balance,
        "pair_symbol": pair_symbol,
        "total_supply": total_supply,
        "share": share,
        "balance_usd": balance_usd,
        "tokens": tokens,
    }
    return pair_info


@ttl_cached()
@handle_exceptions
def portfolio(address):
    address = web3.toChecksumAddress(address)
    # TODO: check if the GraphQL queries can be merged into one
    eth_price = get_eth_price()
    positions = []
    positions += get_liquidity_positions(address)
    positions += get_staking_positions(address)
    balance_usd = 0
    pairs = []
    for position in positions:
        balance = Decimal(position["liquidityTokenBalance"])
        pair = position["pair"]
        pair_info = extract_pair_info(pair, balance, eth_price)
        balance_usd += pair_info["balance_usd"]
        pairs.append(pair_info)
    data = {
        "address": address,
        "pairs": pairs,
        "balance_usd": balance_usd,
    }
    return data


def main():
    parser = argparse.ArgumentParser(description="Liquidity provider portfolio stats.")
    parser.add_argument("address", help="Address")
    args = parser.parse_args()
    address = args.address
    data = portfolio(address)
    pairs = [pair["contract_address"] for pair in data["pairs"]]
    pprint(data)
    data = get_lp_transactions(address, pairs)
    pprint(data)


if __name__ == "__main__":
    main()
