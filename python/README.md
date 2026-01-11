# Python 数据分析模块

链上项目评分协议的 Python 后端，负责复杂的数据分析和评分计算。

## 目录结构

```
python/
├── src/                    # 源代码
│   ├── scoring/           # 评分算法模块
│   ├── blockchain/        # 区块链交互模块
│   └── utils/             # 工具函数
├── tests/                 # 测试文件
├── scripts/               # 执行脚本
├── data/                  # 数据缓存
├── config/                # 配置文件
├── requirements.txt       # 依赖列表
└── pyproject.toml        # 项目配置

```

## 环境配置

### 1. 创建虚拟环境

```bash
cd python
python -m venv venv

# Windows
venv\Scripts\activate

# Linux/Mac
source venv/bin/activate
```

### 2. 安装依赖

```bash
pip install -r requirements.txt
```

### 3. 配置环境变量

```bash
# 复制环境变量模板
cp ../.env.example ../.env

# 编辑 .env 文件，填入真实的配置信息
```

## 核心模块

### scoring/
- **unique_eoa.py** - 独立 EOA 分析
- **holder_analysis.py** - 持有者集中度分析
- **permission_checker.py** - 合约权限检测
- **score_calculator.py** - 综合评分计算

### blockchain/
- **web3_client.py** - Web3 连接客户端
- **contract_reader.py** - 合约数据读取
- **transaction_analyzer.py** - 交易分析

### utils/
- **cache.py** - 数据缓存
- **logger.py** - 日志工具
- **helpers.py** - 辅助函数

## 运行测试

```bash
pytest
```

## 代码格式化

```bash
# 格式化代码
black src/ tests/

# 检查代码质量
flake8 src/ tests/
mypy src/
```
