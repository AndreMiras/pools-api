from unittest import mock

from fastapi.testclient import TestClient
from starlette import status

from .utils import (
    GQL_ETH_PRICE_RESPONSE,
    GQL_LIQUIDITY_POSITIONS_RESPONSE,
    GQL_MINTS_BURNS_TX_RESPONSE,
    GQL_PAIR_INFO_RESPONSE,
    patch_client_execute,
    patch_session_fetch_schema,
    patch_web3_contract,
)


class TestMain:

    address = "0x000000000000000000000000000000000000dEaD"
    url_index = "/"
    url_portfolio = f"/portfolio/{address}"

    def setup_method(self):
        with mock.patch.dict("os.environ", {"WEB3_INFURA_PROJECT_ID": "1"}):
            import libuniswaproi
            from main import app
        self.app = app
        self.libuniswaproi = libuniswaproi
        self.client = TestClient(app)

    def teardown_method(self):
        self.clear_cache()

    def clear_cache(self):
        functions = (
            self.libuniswaproi.get_eth_price,
            self.libuniswaproi.get_liquidity_positions,
            self.libuniswaproi.get_pair_info,
            self.libuniswaproi.get_staking_positions,
            self.libuniswaproi.portfolio,
        )
        for function in functions:
            function.cache_clear()

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
            side_effect=self.libuniswaproi.TheGraphServiceDownException(
                "502 Server Error"
            )
        )
        with mock.patch("libuniswaproi.get_gql_client", m_get_gql_client):
            response = self.client.get(url)
        assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
        assert response.json() == {
            "detail": "The Graph (thegraph.com) is down. 502 Server Error"
        }
