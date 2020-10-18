from decimal import Decimal
from unittest import mock

from .utils import (
    GQL_ETH_PRICE_RESPONSE,
    patch_client_execute,
    patch_session_fetch_schema,
)


class TestLibUniswapRoi:
    def setup_method(self):
        with mock.patch.dict("os.environ", {"WEB3_INFURA_PROJECT_ID": "1"}):
            import libuniswaproi
        self.libuniswaproi = libuniswaproi

    def test_get_eth_price(self):
        m_execute = mock.Mock(return_value=GQL_ETH_PRICE_RESPONSE)
        with patch_client_execute(m_execute), patch_session_fetch_schema():
            eth_price = self.libuniswaproi.get_eth_price()
        assert m_execute.call_count == 1
        assert eth_price == Decimal("321.123")
        assert str(eth_price) == GQL_ETH_PRICE_RESPONSE["bundle"]["ethPrice"]
