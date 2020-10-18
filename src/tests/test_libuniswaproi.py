from decimal import Decimal
from unittest import mock

from .utils import (
    GQL_ETH_PRICE_RESPONSE,
    GQL_PAIR_INFO_RESPONSE,
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

    def test_get_pair_info(self):
        contract_address = "0xA478c2975Ab1Ea89e8196811F51A7B7Ade33eB11"
        m_execute = mock.Mock(return_value=GQL_PAIR_INFO_RESPONSE)
        with patch_client_execute(m_execute), patch_session_fetch_schema():
            pair_info = self.libuniswaproi.get_pair_info(contract_address)
        assert m_execute.call_args_list == [
            mock.call(
                mock.ANY,
                variable_values={"id": contract_address.lower()},
            )
        ]
        assert pair_info["pair"].keys() == {
            "id",
            "reserve0",
            "reserve1",
            "token0",
            "token0Price",
            "token1",
            "token1Price",
            "totalSupply",
        }
