"""
测试独立 EOA 分析模块
"""

import sys
import os

# 添加父目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from src.blockchain.web3_client import Web3Client
from src.scoring.unique_eoa import UniqueEOAAnalyzer


def test_is_eoa():
    """测试 EOA 判断功能"""
    print("=" * 60)
    print("Test 1: EOA Detection")
    print("=" * 60)

    client = Web3Client(network="monad_testnet")
    analyzer = UniqueEOAAnalyzer(client)

    # 测试地址
    test_addresses = [
        "0x0000000000000000000000000000000000000000",  # 零地址 (EOA)
        "0xdf5b718d8fcc173335185a2a1513ee8151e3c027",  # 示例地址
    ]

    for addr in test_addresses:
        is_eoa = analyzer.is_eoa(addr)
        print(f"Address: {addr}")
        print(f"  Is EOA: {is_eoa}")
        print()


def test_scoring_logic():
    """测试评分逻辑"""
    print("=" * 60)
    print("Test 2: Scoring Logic")
    print("=" * 60)

    client = Web3Client(network="monad_testnet")
    analyzer = UniqueEOAAnalyzer(client, use_cache=False)

    # 测试不同 EOA 数量的评分
    test_cases = [
        (10, 1, "Low activity"),
        (50, 1, "Threshold"),
        (150, 1, "Normal"),
        (300, 1, "High activity"),
        (500, 1, "Very high"),
        (100, 2, "2 hours normalized"),
    ]

    print("\nEOA Count | Time (h) | Score | Risk Level | Description")
    print("-" * 70)

    for eoa_count, hours, desc in test_cases:
        score, risk = analyzer._calculate_score(eoa_count, hours)
        print(f"{eoa_count:9} | {hours:8} | {score:5.1f} | {risk:11} | {desc}")


def test_analyze_token():
    """测试真实代币分析（如果有的话）"""
    print("\n" + "=" * 60)
    print("Test 3: Real Token Analysis")
    print("=" * 60)

    try:
        client = Web3Client(network="monad_testnet")
        analyzer = UniqueEOAAnalyzer(client)

        # 获取当前区块
        current_block = client.get_block_number()
        print(f"Current block: {current_block:,}")

        # 分析最近 100 个区块（减少查询时间）
        from_block = max(0, current_block - 100)

        # 这里需要一个真实的代币地址
        # 暂时使用测试地址
        test_token = "0xdf5b718d8fcc173335185a2a1513ee8151e3c027"

        print(f"\nAnalyzing token: {test_token}")
        print(f"Block range: {from_block:,} - {current_block:,}")
        print("\nThis may take a while...")

        result = analyzer.analyze_transfer_events(
            token_address=test_token,
            from_block=from_block,
            to_block=current_block,
            time_window_hours=1
        )

        print("\n--- Analysis Result ---")
        print(f"Events found: {result['events_count']}")
        print(f"Unique EOA: {result['unique_eoa_count']}")
        print(f"Total addresses: {result['total_addresses']}")
        print(f"Contract addresses: {result['contract_addresses']}")
        print(f"EOA percentage: {result['eoa_percentage']:.2f}%")
        print(f"\nScore: {result['score']}/40")
        print(f"Risk Level: {result['risk_level']}")

    except Exception as e:
        print(f"\nWarning: Could not analyze token")
        print(f"Reason: {e}")
        print("This is normal if there are no recent transfers")


def main():
    """运行所有测试"""
    print("\n" + "=" * 60)
    print("UNIQUE EOA ANALYZER - TEST SUITE")
    print("=" * 60 + "\n")

    try:
        # Test 1: EOA 判断
        test_is_eoa()

        # Test 2: 评分逻辑
        test_scoring_logic()

        # Test 3: 真实代币分析（可选）
        test_analyze_token()

        print("\n" + "=" * 60)
        print("All tests completed!")
        print("=" * 60)

    except Exception as e:
        print(f"\nTest failed: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
