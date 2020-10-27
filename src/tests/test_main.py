from unittest import mock

from fastapi.testclient import TestClient
from pools.test_utils import (
    GQL_ETH_PRICE_RESPONSE,
    GQL_LIQUIDITY_POSITIONS_RESPONSE,
    GQL_MINTS_BURNS_TX_RESPONSE,
    GQL_PAIR_DAY_DATA_RESPONSE,
    GQL_PAIR_INFO_RESPONSE,
    GQL_PAIRS_RESPONSE,
    GQL_TOKEN_DAY_DATA_RESPONSE,
    patch_client_execute,
    patch_session_fetch_schema,
    patch_web3_contract,
)
from starlette import status


class TestMain:

    address = "0x000000000000000000000000000000000000dEaD"
    # DAI
    token_address = "0x6B175474E89094C44Da98b954EedeAC495271d0F"
    # DAI-ETH
    pair_address = "0xA478c2975Ab1Ea89e8196811F51A7B7Ade33eB11"
    url_index = "/"
    url_portfolio = f"/portfolio/{address}"
    url_tokens_daily = f"/tokens/{token_address}/daily"
    url_pairs_daily = f"/pairs/{pair_address}/daily"
    url_pairs = "/pairs"

    def setup_method(self):
        with mock.patch.dict("os.environ", {"WEB3_INFURA_PROJECT_ID": "1"}):
            from pools import uniswap

            from main import app
        self.app = app
        self.uniswap = uniswap
        self.client = TestClient(app)

    def teardown_method(self):
        self.clear_cache()

    def clear_cache(self):
        functions = (
            self.uniswap.get_eth_price,
            self.uniswap.get_liquidity_positions,
            self.uniswap.get_pair_info,
            self.uniswap.get_staking_positions,
            self.uniswap.portfolio,
            self.uniswap.get_token_daily_raw,
            self.uniswap.get_pair_daily_raw,
            self.uniswap.get_pairs_raw,
        )
        for function in functions:
            function.cache_clear()

    def test_urls(self):
        """Checks URL patterns."""
        assert self.app.url_path_for("index") == self.url_index
        path_params = {"address": self.address}
        assert self.app.url_path_for("portfolio", **path_params) == self.url_portfolio
        path_params = {"address": self.token_address}
        assert (
            self.app.url_path_for("tokens_daily", **path_params)
            == self.url_tokens_daily
        )
        path_params = {"address": self.pair_address}
        assert (
            self.app.url_path_for("pairs_daily", **path_params) == self.url_pairs_daily
        )
        assert self.app.url_path_for("pairs") == self.url_pairs

    def test_index(self):
        """Index should be redirecting to the documentation."""
        url = self.url_index
        response = self.client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert response.url == "http://testserver/redoc"
        assert "Pools API" in response.text

    def test_portfolio(self):
        """Basic portfolio testing."""
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
        ), patch_session_fetch_schema():
            response = self.client.get(url)
        assert m_contract().functions.balanceOf().call.call_count == 4
        assert m_execute.call_count == 3
        assert response.status_code == status.HTTP_200_OK
        assert response.json().keys() == {"address", "pairs", "balance_usd"}

    def test_portfolio_non_checksum_address(self):
        """Address without checksum should be handled without failing."""
        path_params = {"address": self.address.lower()}
        url = self.app.url_path_for("portfolio", **path_params)
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
        ), patch_session_fetch_schema():
            response = self.client.get(url)
        assert response.status_code == status.HTTP_200_OK

    def test_portfolio_invalid_address(self):
        """Invalid addresses are handled as bad request errors."""
        path_params = {"address": "0xInvalidAdress"}
        url = self.app.url_path_for("portfolio", **path_params)
        response = self.client.get(url)
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.json() == {"detail": "Invalid address 0xInvalidAdress"}

    def test_portfolio_the_graph_bad_gateway(self):
        """The Graph down is a known/caught exception."""
        path_params = {"address": self.address}
        url = self.app.url_path_for("portfolio", **path_params)
        m_get_gql_client = mock.Mock(
            side_effect=self.uniswap.TheGraphServiceDownException("502 Server Error")
        )
        with mock.patch("pools.uniswap.get_gql_client", m_get_gql_client):
            response = self.client.get(url)
        assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
        assert response.json() == {
            "detail": "The Graph (thegraph.com) is down. 502 Server Error"
        }

    def test_tokens_daily(self):
        """Basic tokens daily testing."""
        url = self.url_tokens_daily
        m_execute = mock.Mock(side_effect=(GQL_TOKEN_DAY_DATA_RESPONSE,))
        with patch_client_execute(m_execute), patch_session_fetch_schema():
            response = self.client.get(url)
        assert m_execute.call_count == 1
        assert response.status_code == status.HTTP_200_OK
        assert response.json() == [
            {"date": "2020-10-25T00:00:00", "price_usd": 1.0037},
            {"date": "2020-10-24T00:00:00", "price_usd": 1.0053},
            {"date": "2020-10-23T00:00:00", "price_usd": 1.0063},
            {"date": "2020-10-22T00:00:00", "price_usd": 1.0047},
            {"date": "2020-10-21T00:00:00", "price_usd": 1.0059},
            {"date": "2020-10-20T00:00:00", "price_usd": 1.0049},
        ]

    def test_pairs_daily(self):
        """Basic pairs daily testing."""
        url = self.url_pairs_daily
        m_execute = mock.Mock(side_effect=(GQL_PAIR_DAY_DATA_RESPONSE,))
        with patch_client_execute(m_execute), patch_session_fetch_schema():
            response = self.client.get(url)
        assert m_execute.call_count == 1
        assert response.status_code == status.HTTP_200_OK
        assert response.json() == {
            "pair": {
                "price_usd": 47.63563936389576,
                "reserve_usd": 415905325.9588991,
                "symbol": "DAI-WETH",
                "total_supply": 8730969.742669689,
            },
            "date_price": [
                {"date": "2020-10-25T00:00:00", "price_usd": 47.75974727766944},
                {"date": "2020-10-24T00:00:00", "price_usd": 48.01749402379172},
                {"date": "2020-10-23T00:00:00", "price_usd": 47.88345730523966},
                {"date": "2020-10-22T00:00:00", "price_usd": 48.16869701768363},
                {"date": "2020-10-21T00:00:00", "price_usd": 46.88813260917142},
                {"date": "2020-10-20T00:00:00", "price_usd": 45.415830439697224},
            ],
        }

    def test_pairs(self):
        """Basic pairs testing."""
        url = self.url_pairs
        m_execute = mock.Mock(side_effect=(GQL_PAIRS_RESPONSE,))
        with patch_client_execute(m_execute), patch_session_fetch_schema():
            response = self.client.get(url)
        assert m_execute.call_count == 1
        assert response.status_code == status.HTTP_200_OK
        assert response.json() == [
            {
                "id": "0xc5ddc3e9d103b9dfdf32ae7096f1392cf88696f9",
                "price_usd": 170814795.26734078,
                "symbol": "FCBTC-TWOB",
                "total_supply": 6.764183030477267,
                "reserve_usd": 1155422539.501795,
            },
            {
                "id": "0xbb2b8038a1640196fbe3e38816f3e67cba72d940",
                "price_usd": 500825813.2783621,
                "symbol": "WBTC-WETH",
                "total_supply": 1.3753597279111465,
                "reserve_usd": 688815654.2814068,
            },
            {
                "id": "0xb4e16d0168e52d35cacd2c6185b44281ec28c9dc",
                "price_usd": 50242455.85402316,
                "symbol": "USDC-WETH",
                "total_supply": 12.621500317891401,
                "reserve_usd": 634135172.533198,
            },
        ]
