"""
测试 Web3Client 模块
"""

import pytest
from src.blockchain.web3_client import Web3Client


def test_web3_client_connection():
    """测试连接到 Monad 测试网"""
    try:
        client = Web3Client(network="monad_testnet")
        assert client.is_connected(), "应该成功连接到 Monad 测试网"
        print("✅ 成功连接到 Monad 测试网")
    except Exception as e:
        pytest.fail(f"连接失败: {e}")


def test_get_block_number():
    """测试获取区块高度"""
    client = Web3Client(network="monad_testnet")
    block_number = client.get_block_number()
    assert block_number > 0, "区块高度应该大于 0"
    print(f"✅ 当前区块高度: {block_number}")


def test_get_chain_id():
    """测试获取链 ID"""
    client = Web3Client(network="monad_testnet")
    chain_id = client.get_chain_id()
    assert chain_id == 41454, f"Monad 测试网链 ID 应该是 41454，实际是 {chain_id}"
    print(f"✅ 链 ID: {chain_id}")


def test_is_contract():
    """测试判断地址类型"""
    client = Web3Client(network="monad_testnet")

    # 测试零地址（应该是 EOA）
    zero_address = "0x0000000000000000000000000000000000000000"
    is_contract = client.is_contract(zero_address)
    print(f"✅ 零地址是合约吗: {is_contract}")


def test_checksum_address():
    """测试地址 checksum 转换"""
    client = Web3Client(network="monad_testnet")

    # 测试小写地址
    lowercase = "0x1234567890abcdef1234567890abcdef12345678"
    checksum = client.to_checksum_address(lowercase)
    assert checksum == "0x1234567890AbcdEF1234567890aBcdef12345678", "Checksum 转换错误"
    print(f"✅ Checksum 地址: {checksum}")


if __name__ == "__main__":
    print("=" * 50)
    print("测试 Web3Client 模块")
    print("=" * 50)

    try:
        print("\n[1/5] 测试连接...")
        test_web3_client_connection()

        print("\n[2/5] 测试获取区块高度...")
        test_get_block_number()

        print("\n[3/5] 测试获取链 ID...")
        test_get_chain_id()

        print("\n[4/5] 测试判断合约...")
        test_is_contract()

        print("\n[5/5] 测试地址转换...")
        test_checksum_address()

        print("\n" + "=" * 50)
        print("✅ 所有测试通过！")
        print("=" * 50)

    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
