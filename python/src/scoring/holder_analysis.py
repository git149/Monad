# -*- coding: utf-8 -*-
"""
持有者集中度分析模块

分析代币Top10持有者占比,评估抛压风险 (权重30分)
"""

from typing import Dict, List, Tuple
from blockchain.web3_client import Web3Client
from blockchain.contract_reader import ContractReader
from utils.simple_db import SimpleDB


class HolderAnalyzer:
    """持有者集中度分析器"""

    def __init__(self, client: Web3Client, use_cache: bool = True):
        """
        初始化持有者分析器

        Args:
            client: Web3客户端实例
            use_cache: 是否使用缓存(默认True)
        """
        self.client = client
        self.use_cache = use_cache
        self.db = SimpleDB(db_path="data/holder_cache.db", ttl_hours=1)

    def get_all_holders(
        self, token_address: str, from_block: int = 0, to_block: int = None
    ) -> Dict[str, int]:
        """
        获取所有持有者及其余额

        Args:
            token_address: 代币合约地址
            from_block: 起始区块(0表示创世区块)
            to_block: 结束区块(None表示最新区块)

        Returns:
            {address: balance} 字典
        """
        # 检查缓存
        cache_key = f"holders_{token_address.lower()}"
        if self.use_cache:
            cached = self.db.get(cache_key)
            if cached:
                print("  Using cached holder data...")
                return cached

        print(f"  Fetching all holders from blockchain...")

        # 1. 收集所有出现过的地址
        reader = ContractReader(self.client, token_address)
        if to_block is None:
            to_block = self.client.get_latest_block()

        # 为了避免RPC限制,分批查询(使用较小批次更稳定)
        BATCH_SIZE = 1000  # 降低到1000以避免RPC限制
        all_addresses = set()
        current = from_block

        while current <= to_block:
            batch_end = min(current + BATCH_SIZE, to_block)
            print(f"    Scanning blocks {current} -> {batch_end}...")

            try:
                events = reader.get_transfer_events(current, batch_end)
                for event in events:
                    # 零地址是铸币/销毁,不是真实持有者
                    if event["from"] != "0x0000000000000000000000000000000000000000":
                        all_addresses.add(event["from"])
                    if event["to"] != "0x0000000000000000000000000000000000000000":
                        all_addresses.add(event["to"])

                current = batch_end + 1
            except Exception as e:
                print(f"    ⚠️  Batch query failed: {e}")
                # 如果还是失败,尝试更小的批次
                if "block range too large" in str(e).lower():
                    print(f"    Retrying with smaller batch size...")
                    smaller_batch = (batch_end - current) // 2
                    if smaller_batch < 100:
                        print(f"    Batch too small, skipping range...")
                        current = batch_end + 1
                        continue
                    batch_end = current + smaller_batch
                    try:
                        events = reader.get_transfer_events(current, batch_end)
                        for event in events:
                            if event["from"] != "0x0000000000000000000000000000000000000000":
                                all_addresses.add(event["from"])
                            if event["to"] != "0x0000000000000000000000000000000000000000":
                                all_addresses.add(event["to"])
                        current = batch_end + 1
                    except Exception as retry_e:
                        print(f"    Retry failed: {retry_e}, skipping...")
                        current = batch_end + 1
                        continue
                else:
                    current = batch_end + 1
                    continue

        print(f"  Found {len(all_addresses)} unique addresses")

        # 2. 查询每个地址的当前余额
        holders = {}
        for i, addr in enumerate(all_addresses, 1):
            if i % 50 == 0:
                print(f"    Checking balances... {i}/{len(all_addresses)}")

            try:
                balance = reader.get_balance(addr)
                if balance > 0:
                    holders[addr] = balance
            except Exception as e:
                print(f"    ⚠️  Failed to get balance for {addr[:10]}...: {e}")
                continue

        print(f"  ✅ Found {len(holders)} holders with non-zero balance")

        # 缓存结果
        if self.use_cache:
            self.db.set(cache_key, holders)

        return holders

    def analyze_holder_concentration(
        self, token_address: str, from_block: int = 0, to_block: int = None
    ) -> Dict:
        """
        分析持有者集中度

        Args:
            token_address: 代币合约地址
            from_block: 起始区块
            to_block: 结束区块

        Returns:
            {
                "total_holders": int,
                "total_supply": int,
                "top10_holders": [(address, balance, percentage)],
                "top10_percentage": float,
                "score": float,
                "risk_level": str
            }
        """
        print(f"\n=== Analyzing Holder Concentration ===")

        # 1. 获取所有持有者
        holders = self.get_all_holders(token_address, from_block, to_block)

        if len(holders) == 0:
            return {
                "total_holders": 0,
                "total_supply": 0,
                "top10_holders": [],
                "top10_percentage": 0.0,
                "score": 0.0,
                "risk_level": "unknown",
                "error": "No holders found",
            }

        # 2. 计算总供应量(所有持有者余额之和)
        total_supply = sum(holders.values())

        # 3. 按余额排序,获取Top10
        sorted_holders = sorted(holders.items(), key=lambda x: x[1], reverse=True)
        top10 = sorted_holders[:10]

        # 计算Top10占比
        top10_sum = sum([balance for _, balance in top10])
        top10_percentage = (top10_sum / total_supply * 100) if total_supply > 0 else 0

        # 4. 格式化Top10数据
        top10_formatted = [
            (addr, balance, balance / total_supply * 100) for addr, balance in top10
        ]

        # 5. 计算评分 (权重30分)
        score = self._calculate_score(top10_percentage)

        # 6. 风险等级
        risk_level = self._determine_risk_level(top10_percentage)

        return {
            "total_holders": len(holders),
            "total_supply": total_supply,
            "top10_holders": top10_formatted,
            "top10_percentage": top10_percentage,
            "score": score,
            "risk_level": risk_level,
        }

    def _calculate_score(self, top10_percentage: float) -> float:
        """
        计算评分 (0-30分)

        评分标准:
        - <= 20%: 30分 (健康)
        - 20-40%: 15-30分 (线性递减)
        - > 40%: 0-15分 (线性递减,最高15分)
        """
        if top10_percentage <= 20:
            return 30.0
        elif top10_percentage <= 40:
            # 20-40%之间线性递减: 30 -> 15
            return 30.0 - (top10_percentage - 20) * 0.75
        else:
            # 40%以上继续递减: 15 -> 0
            # 但设定上限,比如80%以上直接0分
            if top10_percentage >= 80:
                return 0.0
            return 15.0 - (top10_percentage - 40) * 0.375

    def _determine_risk_level(self, top10_percentage: float) -> str:
        """
        判断风险等级

        Returns:
            "low_risk" | "medium_risk" | "high_risk" | "extreme_risk"
        """
        if top10_percentage <= 20:
            return "low_risk"
        elif top10_percentage <= 40:
            return "medium_risk"
        elif top10_percentage <= 60:
            return "high_risk"
        else:
            return "extreme_risk"


# 使用示例
if __name__ == "__main__":
    import os
    from dotenv import load_dotenv

    load_dotenv()

    # 连接到Monad主网
    rpc_url = os.getenv("MONAD_MAINNET_RPC_URL")
    client = Web3Client(rpc_url)

    # 测试代币(USDC)
    token_address = "0x754704bc059f8c67012fed69bc8a327a5aafb603"

    # 分析持有者集中度
    analyzer = HolderAnalyzer(client)

    # 注意: 对于USDC这种成熟代币,扫描全量历史会很慢
    # 这里仅作为示例,实际使用时建议:
    # 1. 对新项目: 从创世区块扫描(很快)
    # 2. 对成熟项目: 使用缓存或限制扫描范围

    current_block = client.get_latest_block()
    # 仅扫描最近10000个区块作为演示
    result = analyzer.analyze_holder_concentration(
        token_address, from_block=current_block - 10000, to_block=current_block
    )

    print(f"\n=== Holder Analysis Result ===")
    print(f"Total Holders: {result['total_holders']}")
    print(f"Top10 Percentage: {result['top10_percentage']:.2f}%")
    print(f"Score: {result['score']:.2f}/30")
    print(f"Risk Level: {result['risk_level']}")

    if len(result["top10_holders"]) > 0:
        print(f"\nTop 5 Holders:")
        for i, (addr, balance, pct) in enumerate(result["top10_holders"][:5], 1):
            print(f"  {i}. {addr[:10]}... - {pct:.2f}%")
