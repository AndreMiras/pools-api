from unittest import mock

from fastapi.testclient import TestClient
from starlette import status

GQL_ETH_PRICE_RESPONSE = {"bundle": {"ethPrice": "321.123"}}
GQL_LIQUIDITY_POSITIONS_RESPONSE = {
    "user": {
        "liquidityPositions": [
            {
                "liquidityTokenBalance": "65.417152403305745713",
                "pair": {
                    "id": "0x3b3d4eefdc603b232907a7f3d0ed1eea5c62b5f7",
                    "reserve0": "98885.875625086259763385",
                    "reserve1": "3065.622053657196599417",
                    "token0": {
                        "derivedETH": "0.03100161710940527870014085576340626",
                        "id": "0x0ae055097c6d159879521c384f1d2123d1f195e6",
                        "name": "STAKE",
                        "symbol": "STAKE",
                    },
                    "token0Price": "32.25638186779036564112849328358329",
                    "token1": {
                        "derivedETH": "1",
                        "id": "0xc02aaa39b223fe8d0a0e5c4f27ead9083c756cc2",
                        "name": "Wrapped Ether",
                        "symbol": "WETH",
                    },
                    "token1Price": "0.03100161710940527870014085576340626",
                    "totalSupply": "12132.548610419336726782",
                },
            },
            {
                "liquidityTokenBalance": "123.321",
                "pair": {
                    "id": "0xd3d2e2692501a5c9ca623199d38826e513033a17",
                    "reserve0": "7795837.60970437134772868",
                    "reserve1": "64207.224033613483840543",
                    "token0": {
                        "derivedETH": "0.008236090494456606334236333082884844",
                        "id": "0x1f9840a85d5af5bf1d1762f925bdaddc4201f984",
                        "name": "Uniswap",
                        "symbol": "UNI",
                    },
                    "token0Price": "121.4168300692010713970072022761557",
                    "token1": {
                        "derivedETH": "1",
                        "id": "0xc02aaa39b223fe8d0a0e5c4f27ead9083c756cc2",
                        "name": "Wrapped Ether",
                        "symbol": "WETH",
                    },
                    "token1Price": "0.008236090494456606334236333082884844",
                    "totalSupply": "383443.946054848107867734",
                },
            },
        ]
    }
}

GQL_PAIR_INFO_RESPONSE = {
    "pair": {
        "id": "0xa478c2975ab1ea89e8196811f51a7b7ade33eb11",
        "reserve0": "202079477.297395245222385992",
        "reserve1": "554825.663433614212350256",
        "token0": {
            "derivedETH": "0.002745581445745187399781487618568183",
            "id": "0x6b175474e89094c44da98b954eedeac495271d0f",
            "name": "Dai Stablecoin",
            "symbol": "DAI",
        },
        "token0Price": "364.2215755608687365540815738979592",
        "token1": {
            "derivedETH": "1",
            "id": "0xc02aaa39b223fe8d0a0e5c4f27ead9083c756cc2",
            "name": "Wrapped Ether",
            "symbol": "WETH",
        },
        "token1Price": "0.002745581445745187399781487618568183",
        "totalSupply": "8967094.518364383041536096",
    }
}


GQL_MINTS_BURNS_TX_RESPONSE = {
    "burns": [],
    "mints": [
        {
            "amount0": "15860000",
            "amount1": "600",
            "amountUSD": "229661.2283368789267441858327732994",
            "liquidity": "97549.987186057589967631",
            "pair": {"id": "0xf227e97616063a0ea4143744738f9def2aa06743"},
            "sender": "0x7a250d5630b4cf539739df2c5dacb4c659f2488d",
            "to": "0x000000000000000000000000000000000000dead",
            "transaction": {
                "blockNumber": "11046485",
                "id": "0x7f9080f8c72c0ec21ec7e1690b94c52ebc4787bca66f2d154f62749c5f38fba0",
                "timestamp": "1602581467",
            },
        },
        {
            "amount0": "23188460.096098020166920577",
            "amount1": "1649.824913049740795957",
            "amountUSD": "531596.1714480471128118203674972062",
            "liquidity": "195593.709412655447555532",
            "pair": {"id": "0xc822d85d2dcedfaf2cefcf69dbd5588e7ffc9f10"},
            "sender": "0x7a250d5630b4cf539739df2c5dacb4c659f2488d",
            "to": "0x000000000000000000000000000000000000dead",
            "transaction": {
                "blockNumber": "10543065",
                "id": "0x08d4f7eb1896d9ec25d2d36f72252cdb45f735b922fd1e515e1ce628b3b14e49",
                "timestamp": "1595873620",
            },
        },
    ],
}


def patch_web3_contract(m_contract):
    return mock.patch("experiment.web3.eth.contract", m_contract)


def patch_client_execute(m_execute):
    return mock.patch("experiment.Client.execute", m_execute)


def patch_session_fetch_schema():
    """Bypassing `fetch_schema()` on unit tests."""
    return mock.patch("gql.client.SyncClientSession.fetch_schema")


class TestMain:

    address = "0x000000000000000000000000000000000000dEaD"
    url_index = "/"
    url_portfolio = f"/portfolio/{address}"

    def setup_method(self):
        with mock.patch.dict("os.environ", {"WEB3_INFURA_PROJECT_ID": "1"}):
            from main import app
        self.app = app
        self.client = TestClient(app)

    def test_urls(self):
        """Checks URL patterns."""
        assert self.app.url_path_for("index") == self.url_index
        path_params = {"address": self.address}
        assert self.app.url_path_for("portfolio", **path_params) == self.url_portfolio

    def test_index(self):
        """Index should be redirecting to the documentation."""
        url = self.url_index
        response = self.client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert response.url == "http://testserver/redoc"
        assert "FastAPI - ReDoc" in response.text

    def test_portfolio(self):
        url = self.url_portfolio
        m_contract = mock.Mock()
        m_contract().functions.balanceOf().call.return_value = 0
        m_execute = mock.Mock(
            side_effect=(
                GQL_ETH_PRICE_RESPONSE,
                GQL_LIQUIDITY_POSITIONS_RESPONSE,
                GQL_MINTS_BURNS_TX_RESPONSE,
                GQL_PAIR_INFO_RESPONSE,
            )
        )
        with patch_web3_contract(m_contract), patch_client_execute(
            m_execute
        ) as m_client_execute, patch_session_fetch_schema():
            response = self.client.get(url)
        assert m_contract().functions.balanceOf().call.call_count == 4
        assert m_client_execute.call_count == 3
        assert response.status_code == status.HTTP_200_OK
        assert response.json().keys() == {"address", "pairs", "balance_usd"}
