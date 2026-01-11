"""
Web3 客户端封装
提供简单易用的区块链连接和查询功能
"""

import os
from typing import Optional
from web3 import Web3
from dotenv import load_dotenv


class Web3Client:
    """Web3 客户端封装类"""

    def __init__(self, rpc_url: Optional[str] = None, network: str = "monad_testnet"):
        """
        初始化 Web3 客户端

        Args:
            rpc_url: RPC URL，如果不提供则从环境变量读取
            network: 网络名称 (monad_testnet, bsc_testnet, bsc_mainnet)
        """
        load_dotenv()

        # 如果没有提供 RPC URL，从环境变量读取
        if not rpc_url:
            env_key_map = {
                "monad_testnet": "MONAD_TESTNET_RPC_URL",
                "monad_mainnet": "MONAD_MAINNET_RPC_URL",
                "bsc_testnet": "BSC_TESTNET_RPC_URL",
                "bsc_mainnet": "BSC_MAINNET_RPC_URL",
            }
            env_key = env_key_map.get(network)
            if not env_key:
                raise ValueError(f"Unknown network: {network}")

            rpc_url = os.getenv(env_key)
            if not rpc_url:
                raise ValueError(f"RPC URL not found in .env for {network}")

        # 创建 Web3 实例
        self.w3 = Web3(Web3.HTTPProvider(rpc_url))

        self.network = network
        self.rpc_url = rpc_url

        # 检查连接
        if not self.is_connected():
            raise ConnectionError(f"Failed to connect to {rpc_url}")

    def is_connected(self) -> bool:
        """检查是否已连接到区块链"""
        try:
            return self.w3.is_connected()
        except Exception:
            return False

    def get_balance(self, address: str) -> float:
        """
        获取地址的余额（以 ETH/BNB 为单位）

        Args:
            address: 钱包地址

        Returns:
            余额（单位：ETH/BNB）
        """
        checksum_address = Web3.to_checksum_address(address)
        balance_wei = self.w3.eth.get_balance(checksum_address)
        return float(self.w3.from_wei(balance_wei, "ether"))

    def get_block_number(self) -> int:
        """获取当前区块高度"""
        return self.w3.eth.block_number

    def get_latest_block(self) -> int:
        """获取最新区块高度（别名方法）"""
        return self.get_block_number()

    def get_transaction_count(self, address: str) -> int:
        """
        获取地址的交易计数（nonce）

        Args:
            address: 钱包地址

        Returns:
            交易计数
        """
        checksum_address = Web3.to_checksum_address(address)
        return self.w3.eth.get_transaction_count(checksum_address)

    def get_code(self, address: str) -> str:
        """
        获取合约代码

        Args:
            address: 合约地址

        Returns:
            合约字节码（hex 字符串）
        """
        checksum_address = Web3.to_checksum_address(address)
        code = self.w3.eth.get_code(checksum_address)
        return code.hex()

    def is_contract(self, address: str) -> bool:
        """
        判断地址是否是合约

        Args:
            address: 地址

        Returns:
            True 如果是合约，False 如果是 EOA
        """
        code = self.get_code(address)
        # 如果字节码是 "0x" 或 "0x0"，说明是 EOA
        return len(code) > 2 and code != "0x"

    def get_chain_id(self) -> int:
        """获取链 ID"""
        return self.w3.eth.chain_id

    def to_checksum_address(self, address: str) -> str:
        """
        将地址转换为 checksum 格式

        Args:
            address: 地址

        Returns:
            Checksum 地址
        """
        return Web3.to_checksum_address(address)

    def __repr__(self) -> str:
        """返回客户端信息"""
        status = "connected" if self.is_connected() else "disconnected"
        return f"Web3Client(network={self.network}, status={status})"


# 使用示例
if __name__ == "__main__":
    # 创建客户端
    client = Web3Client(network="monad_testnet")

    print(f"Client: {client}")
    print(f"Chain ID: {client.get_chain_id()}")
    print(f"Block Number: {client.get_block_number()}")

    # 测试一个地址
    test_address = "0xdf5b718d8fcc173335185a2a1513ee8151e3c027"
    print(f"Is contract: {client.is_contract(test_address)}")
