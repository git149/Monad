# Monad 链上项目评分协议

Monad Hackathon 的链上项目评分协议（On-chain Project Scoring Protocol）- 通过分析链上数据提供可信的项目风险评估。

## 项目简介

本项目旨在通过分析链上行为而非营销材料，为 Web3 项目提供客观、可验证的风险评分，帮助投资者识别潜在的 Rug Pull 和中心化风险。

## 技术栈

### 区块链层 (Solidity)
- **Solidity 0.8.20** - 智能合约开发
- **OpenZeppelin 4.9** - 合约库和标准
- **Foundry** - 开发框架
- **Monad Blockchain** - 最终部署目标（高 TPS EVM 兼容链）

### 后端/数据处理 (Python)
- **Python 3.10+** - 复杂计算和数据分析
- **Web3.py** - 区块链交互
- **Pandas** - 数据处理
- **SQLite** - 本地数据缓存

## 项目结构

```
Monadgame/
├── solidity/              # Solidity 智能合约
│   ├── src/              # 合约源代码
│   ├── test/             # 合约测试
│   ├── script/           # 部署脚本
│   ├── lib/              # 依赖库
│   └── foundry.toml      # Foundry 配置
│
├── python/               # Python 数据分析模块
│   ├── src/             # Python 源代码
│   │   ├── scoring/     # 评分算法
│   │   ├── blockchain/  # 区块链交互
│   │   └── utils/       # 工具函数
│   ├── tests/           # Python 测试
│   ├── config/          # 配置文件
│   └── requirements.txt # Python 依赖
│
├── docs/                # 项目文档
├── .env.example         # 环境变量模板
└── README.md           # 项目说明

```

## 核心功能

1. **独立 EOA 分析** (40分权重)
   - 统计独立外部账户数量
   - 检测虚假活跃度和刷量行为

2. **Top 10 持有者集中度** (30分权重)
   - 分析代币分布情况
   - 识别中心化和 Rug Pull 风险

3. **智能合约权限检测** (30分权重)
   - 检测危险函数（mint、setTax、upgradeTo）
   - 评估合约安全性

## 快速开始

### 1. 环境配置

```bash
# 克隆项目
git clone <repository-url>
cd Monadgame

# 复制环境变量
cp .env.example .env
# 编辑 .env 填入真实配置
```

### 2. Solidity 开发环境

```bash
cd solidity

# 安装依赖（已自动安装）
forge install

# 编译合约
forge build

# 运行测试
forge test
```

### 3. Python 开发环境

```bash
cd python

# 创建虚拟环境
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 安装依赖
pip install -r requirements.txt

# 运行测试
pytest
```

## 评分系统

- **80-100分**: 结构健康，风险较低
- **60-80分**: 存在结构性风险
- **<40分**: 高风险项目，建议谨慎

## 开发路线

- [x] 项目初始化和架构设计
- [x] Foundry 框架配置
- [x] Python 环境搭建
- [ ] 智能合约开发
- [ ] Python 评分算法实现
- [ ] 测试网部署
- [ ] Monad 主网部署

## 贡献指南

请查看 [docs/](docs/) 目录获取更多开发文档和规范。

## License

MIT
