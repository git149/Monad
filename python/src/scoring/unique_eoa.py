"""
独立 EOA 分析模块
统计代币合约在特定时间段内的独立外部账户（EOA）数量
用于检测虚假活跃度和刷量行为

评分权重: 40分
核心逻辑: 在 Monad 这种高 TPS 链上，刷交易数量很容易，但刷独立 EOA 很难
"""

from typing import Dict, List, Set, Optional
from collections import defaultdict
from datetime import datetime, timedelta

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from src.blockchain.web3_client import Web3Client
from src.blockchain.contract_reader import ContractReader
from src.utils.simple_db import SimpleDB


class UniqueEOAAnalyzer:
    """独立 EOA 分析器"""

    def __init__(self, client: Web3Client, use_cache: bool = True):
        """
        初始化 EOA 分析器

        Args:
            client: Web3 客户端实例
            use_cache: 是否使用缓存（默认 True）
        """
        self.client = client
        self.cache = SimpleDB() if use_cache else None

    def is_eoa(self, address: str) -> bool:
        """
        判断地址是否是 EOA（外部账户）

        Args:
            address: 地址

        Returns:
            True 如果是 EOA，False 如果是合约

        注意：
        - EOA: 代码为空 (get_code == '0x')
        - 合约: 有字节码
        - 黑客松阶段这个判定够用了
        """
        # 先检查缓存
        if self.cache:
            cache_key = f"is_eoa_{address.lower()}"
            cached = self.cache.get(cache_key)
            if cached is not None:
                return cached

        # 判断是否是合约
        is_contract = self.client.is_contract(address)
        result = not is_contract

        # 缓存结果（EOA/合约身份不会改变）
        if self.cache:
            self.cache.set(cache_key, result)

        return result

    def analyze_transfer_events(
        self,
        token_address: str,
        from_block: int,
        to_block: Optional[int] = None,
        time_window_hours: int = 1
    ) -> Dict:
        """
        分析代币的 Transfer 事件，统计独立 EOA

        Args:
            token_address: 代币合约地址
            from_block: 起始区块
            to_block: 结束区块（None = 最新区块）
            time_window_hours: 时间窗口（小时）

        Returns:
            分析结果字典，包含：
            - unique_eoa_count: 独立 EOA 数量
            - unique_eoa_list: EOA 地址列表
            - total_addresses: 所有参与地址数
            - contract_addresses: 合约地址数量
            - score: 评分（0-40）
            - risk_level: 风险等级
        """
        # 创建合约读取器
        reader = ContractReader(self.client, token_address)

        # 获取 Transfer 事件
        print(f"Fetching Transfer events from block {from_block} to {to_block}...")
        events = reader.get_transfer_events(from_block, to_block)

        if not events:
            return {
                "unique_eoa_count": 0,
                "unique_eoa_list": [],
                "total_addresses": 0,
                "contract_addresses": 0,
                "score": 0,
                "risk_level": "high_risk",
                "message": "No transfer events found"
            }

        # 统计所有地址
        all_addresses = set()
        eoa_addresses = set()
        contract_addresses = set()

        print(f"Analyzing {len(events)} transfer events...")

        for i, event in enumerate(events):
            # 进度提示
            if (i + 1) % 100 == 0:
                print(f"  Processed {i + 1}/{len(events)} events...")

            from_addr = event["from"]
            to_addr = event["to"]

            # 收集所有地址
            all_addresses.add(from_addr)
            all_addresses.add(to_addr)

            # 判断 from 地址
            if self.is_eoa(from_addr):
                eoa_addresses.add(from_addr)
            else:
                contract_addresses.add(from_addr)

            # 判断 to 地址
            if self.is_eoa(to_addr):
                eoa_addresses.add(to_addr)
            else:
                contract_addresses.add(to_addr)

        # 计算评分
        unique_eoa_count = len(eoa_addresses)
        score, risk_level = self._calculate_score(unique_eoa_count, time_window_hours)

        return {
            "unique_eoa_count": unique_eoa_count,
            "unique_eoa_list": list(eoa_addresses),
            "total_addresses": len(all_addresses),
            "contract_addresses": len(contract_addresses),
            "eoa_percentage": unique_eoa_count / len(all_addresses) * 100 if all_addresses else 0,
            "score": score,
            "risk_level": risk_level,
            "time_window_hours": time_window_hours,
            "blocks_analyzed": f"{from_block} - {to_block or 'latest'}",
            "events_count": len(events)
        }

    def _calculate_score(self, unique_eoa_count: int, time_window_hours: int) -> tuple:
        """
        根据独立 EOA 数量计算评分

        评分标准（黑客松阈值）:
        - 1小时 > 300 EOA: 高活跃，40分
        - 1小时 50-300 EOA: 正常，20-40分线性
        - 1小时 < 50 EOA: 疑似刷量，0-20分

        Args:
            unique_eoa_count: 独立 EOA 数量
            time_window_hours: 时间窗口（小时）

        Returns:
            (score, risk_level) 元组
        """
        # 标准化到 1 小时
        normalized_count = unique_eoa_count / time_window_hours

        if normalized_count >= 300:
            # 高活跃：40分
            score = 40
            risk_level = "low_risk"
        elif normalized_count >= 50:
            # 正常：20-40分线性插值
            # score = 20 + (normalized_count - 50) / (300 - 50) * 20
            score = 20 + (normalized_count - 50) / 250 * 20
            risk_level = "medium_risk"
        else:
            # 疑似刷量：0-20分
            score = (normalized_count / 50) * 20
            risk_level = "high_risk"

        return round(score, 2), risk_level

    def get_eoa_activity_stats(self, token_address: str, from_block: int, to_block: Optional[int] = None) -> Dict:
        """
        获取 EOA 活动统计（扩展分析）

        Args:
            token_address: 代币地址
            from_block: 起始区块
            to_block: 结束区块

        Returns:
            EOA 活动统计字典
        """
        reader = ContractReader(self.client, token_address)
        events = reader.get_transfer_events(from_block, to_block)

        # 统计每个 EOA 的交易次数
        eoa_tx_count = defaultdict(int)

        for event in events:
            from_addr = event["from"]
            to_addr = event["to"]

            if self.is_eoa(from_addr):
                eoa_tx_count[from_addr] += 1
            if self.is_eoa(to_addr):
                eoa_tx_count[to_addr] += 1

        if not eoa_tx_count:
            return {
                "total_eoa": 0,
                "avg_tx_per_eoa": 0,
                "high_frequency_eoa": 0,
                "single_tx_eoa": 0
            }

        # 分析
        total_eoa = len(eoa_tx_count)
        avg_tx = sum(eoa_tx_count.values()) / total_eoa
        high_freq = sum(1 for count in eoa_tx_count.values() if count > 10)
        single_tx = sum(1 for count in eoa_tx_count.values() if count == 1)

        return {
            "total_eoa": total_eoa,
            "avg_tx_per_eoa": round(avg_tx, 2),
            "high_frequency_eoa": high_freq,  # 超过10次交易的EOA
            "single_tx_eoa": single_tx,  # 只有1次交易的EOA
            "high_freq_percentage": round(high_freq / total_eoa * 100, 2),
            "single_tx_percentage": round(single_tx / total_eoa * 100, 2)
        }


# 使用示例
if __name__ == "__main__":
    from dotenv import load_dotenv
    load_dotenv()

    # 创建 Web3 客户端
    client = Web3Client(network="monad_testnet")

    # 创建分析器
    analyzer = UniqueEOAAnalyzer(client)

    # 测试分析（需要一个真实的代币地址）
    # 这里使用一个示例地址，实际使用时替换
    test_token = "0xdf5b718d8fcc173335185a2a1513ee8151e3c027"

    # 获取最近的区块范围（比如最近1000个区块）
    current_block = client.get_block_number()
    from_block = max(0, current_block - 1000)

    print(f"Analyzing token: {test_token}")
    print(f"Block range: {from_block} - {current_block}")

    # 执行分析
    result = analyzer.analyze_transfer_events(
        token_address=test_token,
        from_block=from_block,
        to_block=current_block,
        time_window_hours=1
    )

    print("\n=== Analysis Result ===")
    print(f"Unique EOA Count: {result['unique_eoa_count']}")
    print(f"Total Addresses: {result['total_addresses']}")
    print(f"Contract Addresses: {result['contract_addresses']}")
    print(f"EOA Percentage: {result['eoa_percentage']:.2f}%")
    print(f"Score: {result['score']}/40")
    print(f"Risk Level: {result['risk_level']}")
