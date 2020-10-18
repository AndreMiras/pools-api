from decimal import Decimal
from unittest import mock

from .utils import (
    GQL_ETH_PRICE_RESPONSE,
    GQL_LIQUIDITY_POSITIONS_RESPONSE,
    GQL_PAIR_INFO_RESPONSE,
    patch_client_execute,
    patch_session_fetch_schema,
    patch_web3_contract,
)


class TestLibUniswapRoi:
    address = "0x000000000000000000000000000000000000dEaD"
    contract_address = "0xA478c2975Ab1Ea89e8196811F51A7B7Ade33eB11"

    def setup_method(self):
        with mock.patch.dict("os.environ", {"WEB3_INFURA_PROJECT_ID": "1"}):
            import libuniswaproi
        self.libuniswaproi = libuniswaproi

    def teardown_method(self):
        self.clear_cache()

    def clear_cache(self):
        functions = (
            self.libuniswaproi.get_eth_price,
            self.libuniswaproi.get_liquidity_positions,
            self.libuniswaproi.get_pair_info,
            self.libuniswaproi.get_staking_positions,
        )
        for function in functions:
            function.cache_clear()

    def test_get_eth_price(self):
        m_execute = mock.Mock(return_value=GQL_ETH_PRICE_RESPONSE)
        with patch_client_execute(m_execute), patch_session_fetch_schema():
            eth_price = self.libuniswaproi.get_eth_price()
        assert m_execute.call_count == 1
        assert eth_price == Decimal("321.123")
        assert str(eth_price) == GQL_ETH_PRICE_RESPONSE["bundle"]["ethPrice"]

    def test_get_pair_info(self):
        m_execute = mock.Mock(return_value=GQL_PAIR_INFO_RESPONSE)
        with patch_client_execute(m_execute), patch_session_fetch_schema():
            pair_info = self.libuniswaproi.get_pair_info(self.contract_address)
        assert m_execute.call_args_list == [
            mock.call(
                mock.ANY,
                variable_values={"id": self.contract_address.lower()},
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

    def test_get_liquidity_positions(self):
        m_execute = mock.Mock(return_value=GQL_LIQUIDITY_POSITIONS_RESPONSE)
        with patch_client_execute(m_execute), patch_session_fetch_schema():
            positions = self.libuniswaproi.get_liquidity_positions(self.address)
        assert m_execute.call_args_list == [
            mock.call(
                mock.ANY,
                variable_values={"id": self.address.lower()},
            )
        ]
        assert len(positions) == 2
        assert positions[0].keys() == {"liquidityTokenBalance", "pair"}

    def test_get_liquidity_positions_no_liquidity(self):
        """Makes sure the function doesn't crash on no liquidity positions."""
        m_execute = mock.Mock(return_value={"user": None})
        with patch_client_execute(m_execute), patch_session_fetch_schema():
            positions = self.libuniswaproi.get_liquidity_positions(self.address)
        assert m_execute.call_args_list == [
            mock.call(
                mock.ANY,
                variable_values={"id": self.address.lower()},
            )
        ]
        assert positions == []

    def test_get_staking_positions(self):
        m_contract = mock.Mock()
        m_contract().functions.balanceOf().call.return_value = 0
        with patch_web3_contract(m_contract):
            positions = self.libuniswaproi.get_staking_positions(self.address)
        assert m_contract().functions.balanceOf().call.call_count == 4
        assert len(positions) == 0
