"""
合约读取器
用于读取 ERC20 代币合约的信息和事件
"""

from typing import Dict, List, Optional, Any
from web3 import Web3
from web3.contract import Contract
from .web3_client import Web3Client


# 标准 ERC20 ABI（简化版，只包含需要的函数）
ERC20_ABI = [
    {
        "constant": True,
        "inputs": [],
        "name": "name",
        "outputs": [{"name": "", "type": "string"}],
        "type": "function"
    },
    {
        "constant": True,
        "inputs": [],
        "name": "symbol",
        "outputs": [{"name": "", "type": "string"}],
        "type": "function"
    },
    {
        "constant": True,
        "inputs": [],
        "name": "decimals",
        "outputs": [{"name": "", "type": "uint8"}],
        "type": "function"
    },
    {
        "constant": True,
        "inputs": [],
        "name": "totalSupply",
        "outputs": [{"name": "", "type": "uint256"}],
        "type": "function"
    },
    {
        "constant": True,
        "inputs": [{"name": "account", "type": "address"}],
        "name": "balanceOf",
        "outputs": [{"name": "", "type": "uint256"}],
        "type": "function"
    },
    {
        "anonymous": False,
        "inputs": [
            {"indexed": True, "name": "from", "type": "address"},
            {"indexed": True, "name": "to", "type": "address"},
            {"indexed": False, "name": "value", "type": "uint256"}
        ],
        "name": "Transfer",
        "type": "event"
    }
]


class ContractReader:
    """ERC20 合约读取器"""

    def __init__(self, client: Web3Client, contract_address: str):
        """
        初始化合约读取器

        Args:
            client: Web3 客户端实例
            contract_address: 合约地址
        """
        self.client = client
        self.contract_address = Web3.to_checksum_address(contract_address)

        # 创建合约实例
        self.contract: Contract = client.w3.eth.contract(
            address=self.contract_address,
            abi=ERC20_ABI
        )

    def get_name(self) -> str:
        """获取代币名称"""
        try:
            return self.contract.functions.name().call()
        except Exception:
            return "Unknown"

    def get_symbol(self) -> str:
        """获取代币符号"""
        try:
            return self.contract.functions.symbol().call()
        except Exception:
            return "UNKNOWN"

    def get_decimals(self) -> int:
        """获取代币小数位数"""
        try:
            return self.contract.functions.decimals().call()
        except Exception:
            return 18  # 默认 18 位

    def get_total_supply(self) -> int:
        """获取代币总供应量（原始值，未除以 decimals）"""
        try:
            return self.contract.functions.totalSupply().call()
        except Exception:
            return 0

    def get_total_supply_human(self) -> float:
        """获取代币总供应量（人类可读格式）"""
        total_supply = self.get_total_supply()
        decimals = self.get_decimals()
        return total_supply / (10 ** decimals)

    def get_balance(self, address: str) -> int:
        """
        获取地址的代币余额（原始值）

        Args:
            address: 钱包地址

        Returns:
            代币余额（原始值）
        """
        checksum_address = Web3.to_checksum_address(address)
        try:
            return self.contract.functions.balanceOf(checksum_address).call()
        except Exception:
            return 0

    def get_balance_human(self, address: str) -> float:
        """
        获取地址的代币余额（人类可读格式）

        Args:
            address: 钱包地址

        Returns:
            代币余额（除以 decimals 后的值）
        """
        balance = self.get_balance(address)
        decimals = self.get_decimals()
        return balance / (10 ** decimals)

    def get_transfer_events(
        self,
        from_block: int = 0,
        to_block: Optional[int] = None,
        from_address: Optional[str] = None,
        to_address: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        获取 Transfer 事件

        Args:
            from_block: 起始区块
            to_block: 结束区块（None 表示最新区块）
            from_address: 发送方地址过滤
            to_address: 接收方地址过滤

        Returns:
            Transfer 事件列表
        """
        if to_block is None:
            to_block = self.client.get_block_number()

        # 构建过滤器参数（Web3.py 6.x 使用下划线命名）
        filter_params = {
            "from_block": from_block,
            "to_block": to_block
        }

        if from_address:
            filter_params["argument_filters"] = {"from": Web3.to_checksum_address(from_address)}
        if to_address:
            if "argument_filters" not in filter_params:
                filter_params["argument_filters"] = {}
            filter_params["argument_filters"]["to"] = Web3.to_checksum_address(to_address)

        try:
            # 使用 getLogs 直接查询（Monad 不支持 filter API）
            # 构建事件签名
            transfer_topic = self.client.w3.keccak(text="Transfer(address,address,uint256)").hex()

            logs_params = {
                "fromBlock": hex(from_block),
                "toBlock": hex(to_block),
                "address": self.contract_address,
                "topics": [transfer_topic]
            }

            # 直接调用 eth_getLogs
            logs = self.client.w3.eth.get_logs(logs_params)

            # 格式化事件数据
            formatted_events = []
            for log in logs:
                try:
                    # 解码事件数据
                    event_data = self.contract.events.Transfer().process_log(log)

                    formatted_events.append({
                        "block_number": event_data["blockNumber"],
                        "transaction_hash": event_data["transactionHash"].hex(),
                        "from": event_data["args"]["from"],
                        "to": event_data["args"]["to"],
                        "value": event_data["args"]["value"]
                    })
                except Exception as decode_error:
                    # 跳过无法解码的日志
                    continue

            return formatted_events

        except Exception as e:
            print(f"Error fetching events: {e}")
            return []

    def get_token_info(self) -> Dict[str, Any]:
        """
        获取代币完整信息

        Returns:
            包含代币信息的字典
        """
        return {
            "address": self.contract_address,
            "name": self.get_name(),
            "symbol": self.get_symbol(),
            "decimals": self.get_decimals(),
            "total_supply": self.get_total_supply(),
            "total_supply_human": self.get_total_supply_human()
        }

    def __repr__(self) -> str:
        """返回合约信息"""
        try:
            symbol = self.get_symbol()
            return f"ContractReader(token={symbol}, address={self.contract_address})"
        except Exception:
            return f"ContractReader(address={self.contract_address})"


# 使用示例
if __name__ == "__main__":
    from dotenv import load_dotenv
    load_dotenv()

    # 创建客户端
    client = Web3Client(network="bsc_testnet")

    # 测试一个 BSC 测试网的代币合约（BUSD）
    test_token = "0x8301F2213c0eeD49a7E28Ae4c3e91722919B8B47"

    # 创建合约读取器
    reader = ContractReader(client, test_token)

    # 获取代币信息
    info = reader.get_token_info()
    print(f"Token Info: {info}")
