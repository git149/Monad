# -*- coding: utf-8 -*-
"""
模块测试脚本

测试所有已开发的核心模块功能
"""

import os
import sys

# 设置输出编码为 UTF-8（Windows 兼容）
if sys.platform == 'win32':
    import codecs
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
    sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')

from dotenv import load_dotenv

# 添加 src 目录到 Python 路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

from blockchain.web3_client import Web3Client
from blockchain.contract_reader import ContractReader
from scoring.unique_eoa import UniqueEOAAnalyzer
from utils.simple_db import SimpleDB


def print_section(title: str):
    """打印分隔线"""
    print("\n" + "=" * 70)
    print(f" {title}")
    print("=" * 70)


def test_web3_client(rpc_url: str):
    """测试 Web3 客户端"""
    print_section("1. 测试 Web3 客户端")

    try:
        client = Web3Client(rpc_url)
        print(f"✅ Web3 客户端初始化成功")
        print(f"   RPC: {rpc_url}")

        # 测试连接
        if client.is_connected():
            print(f"✅ RPC 连接正常")
        else:
            print(f"❌ RPC 连接失败")
            return None

        # 获取最新区块
        latest_block = client.get_latest_block()
        print(f"✅ 最新区块: {latest_block}")

        # 测试地址检测
        test_addresses = {
            "0x0000000000000000000000000000000000000000": "零地址",
            "0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb": "普通地址",
        }

        for addr, desc in test_addresses.items():
            try:
                is_contract = client.is_contract(addr)
                addr_type = "合约" if is_contract else "EOA"
                print(f"   {desc} ({addr[:10]}...): {addr_type}")
            except Exception as e:
                print(f"   {desc}: 检测失败 - {e}")

        return client

    except Exception as e:
        print(f"❌ Web3 客户端测试失败: {e}")
        return None


def test_contract_reader(client: Web3Client, token_address: str):
    """测试合约读取器"""
    print_section("2. 测试合约读取器")

    try:
        reader = ContractReader(client, token_address)
        print(f"✅ 合约读取器初始化成功")
        print(f"   代币地址: {token_address}")

        # 读取代币信息
        try:
            name = reader.get_name()
            symbol = reader.get_symbol()
            decimals = reader.get_decimals()
            total_supply = reader.get_total_supply_human()

            print(f"\n代币信息:")
            print(f"   名称: {name}")
            print(f"   符号: {symbol}")
            print(f"   精度: {decimals}")
            print(f"   总供应量: {total_supply:,.2f}")
        except Exception as e:
            print(f"⚠️  无法读取代币信息: {e}")

        # 获取 Transfer 事件
        try:
            current_block = client.get_latest_block()
            from_block = max(0, current_block - 1000)  # 最近 1000 个区块(避免RPC限制)

            print(f"\n获取 Transfer 事件 (区块 {from_block} -> {current_block}):")
            events = reader.get_transfer_events(from_block, current_block)
            print(f"✅ 获取到 {len(events)} 个 Transfer 事件")

            if len(events) > 0:
                print(f"\n最近 3 个事件:")
                for i, event in enumerate(events[:3], 1):
                    print(f"   {i}. 区块 {event['block_number']}")
                    print(f"      从: {event['from'][:10]}...")
                    print(f"      到: {event['to'][:10]}...")
                    print(f"      数量: {event['value']}")
            else:
                print(f"⚠️  该时间段内没有 Transfer 事件")

        except Exception as e:
            print(f"⚠️  获取 Transfer 事件失败: {e}")

        return reader

    except Exception as e:
        print(f"❌ 合约读取器测试失败: {e}")
        return None


def test_unique_eoa_analyzer(client: Web3Client, token_address: str):
    """测试独立 EOA 分析器"""
    print_section("3. 测试独立 EOA 分析器")

    try:
        analyzer = UniqueEOAAnalyzer(client)
        print(f"✅ EOA 分析器初始化成功")

        # 分析最近 1000 个区块(避免RPC block range限制)
        current_block = client.get_latest_block()
        blocks_to_analyze = 1000
        from_block = max(0, current_block - blocks_to_analyze)

        print(f"\n分析区块范围: {from_block} -> {current_block}")
        print(f"区块数量: {blocks_to_analyze}")

        result = analyzer.analyze_transfer_events(
            token_address=token_address,
            from_block=from_block,
            to_block=current_block,
            time_window_hours=1
        )

        print(f"\n分析结果:")
        print(f"   Transfer事件数: {result['events_count']}")
        print(f"   总参与地址数: {result['total_addresses']}")
        print(f"   独立 EOA 数量: {result['unique_eoa_count']}")
        print(f"   合约地址数量: {result['contract_addresses']}")
        print(f"   EOA 占比: {result['eoa_percentage']:.2f}%")
        print(f"   评分: {result['score']}/40")
        print(f"   风险等级: {result['risk_level']}")

        if result["unique_eoa_count"] > 0:
            print(f"\n前 5 个活跃 EOA:")
            for i, addr in enumerate(result["unique_eoa_list"][:5], 1):
                print(f"   {i}. {addr[:20]}...")
        else:
            print(f"\n⚠️  该时间段内没有检测到独立 EOA 活动")

        return result

    except Exception as e:
        print(f"❌ EOA 分析器测试失败: {e}")
        import traceback

        traceback.print_exc()
        return None


def test_database():
    """测试数据库缓存"""
    print_section("4. 测试数据库缓存")

    try:
        db = SimpleDB()
        print(f"✅ 数据库初始化成功")

        # 写入测试数据
        test_key = "test_key"
        test_data = {"message": "Hello, World!", "value": 12345}

        db.set(test_key, test_data)
        print(f"✅ 写入测试数据: {test_key}")

        # 读取数据
        retrieved = db.get(test_key)
        if retrieved == test_data:
            print(f"✅ 读取数据成功: {retrieved}")
        else:
            print(f"❌ 读取数据失败: 期望 {test_data}, 实际 {retrieved}")

        # 测试过期数据（使用 ttl_hours=0 的新实例）
        db_short_ttl = SimpleDB(db_path="data/test_cache.db", ttl_hours=0)
        db_short_ttl.set("expired_key", "will expire")
        import time

        time.sleep(1)
        expired_data = db_short_ttl.get("expired_key")
        if expired_data is None:
            print(f"✅ 过期数据自动清理成功")
        else:
            print(f"⚠️  过期数据未被清理: {expired_data}")

        # 清理测试数据
        db.clear()
        print(f"✅ 数据库清理完成")

    except Exception as e:
        print(f"❌ 数据库测试失败: {e}")


def main():
    """主测试函数"""
    print("=" * 70)
    print(" Monad 项目评分协议 - 模块测试")
    print("=" * 70)

    # 加载环境变量（从项目根目录读取）
    env_path = os.path.join(os.path.dirname(__file__), "..", ".env")
    load_dotenv(env_path)
    print(f"环境变量文件: {os.path.abspath(env_path)}\n")

    # 优先使用主网 RPC
    rpc_url = os.getenv("MONAD_MAINNET_RPC_URL") or os.getenv("MONAD_TESTNET_RPC_URL")
    token_address = os.getenv("TEST_TOKEN_ADDRESS")

    if not rpc_url:
        print("❌ 错误: 未设置 MONAD_TESTNET_RPC_URL 环境变量")
        print("   请在 .env 文件中设置 RPC URL")
        return

    if not token_address:
        print("⚠️  警告: 未设置 TEST_TOKEN_ADDRESS 环境变量")
        print("   部分测试将被跳过")

    # 1. 测试 Web3 客户端
    client = test_web3_client(rpc_url)
    if not client:
        print("\n❌ Web3 客户端测试失败，终止测试")
        return

    # 2. 测试合约读取器（如果有代币地址）
    if token_address:
        test_contract_reader(client, token_address)
        test_unique_eoa_analyzer(client, token_address)
    else:
        print("\n⚠️  跳过合约相关测试（未设置 TEST_TOKEN_ADDRESS）")

    # 3. 测试数据库
    test_database()

    # 总结
    print_section("测试完成")
    print("✅ 所有模块测试完成!")
    print("\n已开发模块清单:")
    print("  [✅] blockchain/web3_client.py - Web3 连接管理")
    print("  [✅] blockchain/contract_reader.py - ERC20 合约读取")
    print("  [✅] scoring/unique_eoa.py - 独立 EOA 分析 (40分)")
    print("  [✅] utils/simple_db.py - SQLite 缓存")
    print("\n待开发模块:")
    print("  [ ] scoring/holder_analysis.py - 持有者集中度分析 (30分)")
    print("  [ ] scoring/permission_checker.py - 合约权限检测 (30分)")
    print("  [ ] scoring/score_calculator.py - 综合评分计算器")


if __name__ == "__main__":
    main()
