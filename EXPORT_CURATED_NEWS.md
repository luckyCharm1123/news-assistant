# AI精选新闻导出工具使用说明

## 📋 概述

`export_curated_news.py` 是一个用于导出AI精选新闻到CSV文件的工具。

## 🎯 功能特点

- ✅ 支持导出所有AI精选新闻或指定数量
- ✅ 两种导出模式：简化版和详细版
- ✅ 自动生成带时间戳的文件名
- ✅ UTF-8编码，Excel友好
- ✅ 包含原始新闻关联信息

## 📊 数据库表结构

AI精选新闻表（`curated_news`）包含以下字段：

| 字段 | 类型 | 说明 |
|------|------|------|
| id | INTEGER | 主键ID |
| title | TEXT | AI生成的标题（带分类标签） |
| source_news_id | INTEGER | 原始新闻ID |
| summary | TEXT | 新闻摘要 |
| merged_from | TEXT | 合并来源ID列表（JSON） |
| is_merged | BOOLEAN | 是否已被合并 |
| merged_into_id | INTEGER | 被合并到的记录ID |
| created_at | TIMESTAMP | 创建时间 |
| updated_at | TIMESTAMP | 更新时间 |

## 🚀 使用方法

### 基本用法

```bash
# 导出所有数据（简化版）
python3 export_curated_news.py

# 导出所有数据（详细版，包含更多信息）
python3 export_curated_news.py --detailed

# 导出指定数量
python3 export_curated_news.py --limit 50

# 指定输出文件名
python3 export_curated_news.py --output my_news.csv

# 组合使用
python3 export_curated_news.py -l 30 -o latest_30.csv -d
```

### 参数说明

| 参数 | 简写 | 说明 | 默认值 |
|------|------|------|--------|
| --db | - | 数据库文件路径 | data/hotnews.db |
| --output | -o | 输出CSV文件路径 | 自动生成（带时间戳） |
| --limit | -l | 导出条数限制 | 全部 |
| --detailed | -d | 导出详细版 | 否 |

### 示例场景

**场景1: 导出最新50条新闻**
```bash
python3 export_curated_news.py --limit 50 --output latest_50.csv
```

**场景2: 导出完整数据用于分析**
```bash
python3 export_curated_news.py --detailed --output full_data.csv
```

**场景3: 定时导出（使用cron）**
```bash
# 每天凌晨2点导出
0 2 * * * cd /path/to/hotnews_crawler && python3 export_curated_news.py
```

## 📁 输出文件说明

### 简化版 CSV

默认导出的简化版本，包含以下列：

1. **AI精选ID** - curated_news表的ID
2. **AI精选标题** - AI生成的标题（如【投资市场】...）
3. **摘要** - 新闻摘要内容
4. **原始新闻ID** - 原始news表的ID
5. **原始新闻标题** - 原始新闻标题
6. **来源** - 新闻来源网站
7. **URL** - 新闻链接
8. **创建时间** - AI精选新闻创建时间
9. **更新时间** - AI精选新闻最后更新时间

### 详细版 CSV

使用 `--detailed` 参数导出的详细版本，额外包含：

- **爬取时间** - 原始新闻的爬取时间
- 更完整的时间戳信息
- 保留所有原始字段

## 📈 数据统计示例

```bash
# 查看数据库中有多少条AI精选新闻
python3 -c "
import sys
sys.path.insert(0, 'src')
from database import DatabaseManager
db = DatabaseManager('data/hotnews.db')
print(f'总计: {db.get_curated_news_count()} 条')
"
```

## 🔍 CSV文件预览

生成的CSV文件可以直接用Excel、WPS或任何文本编辑器打开：

```csv
AI精选ID,AI精选标题,摘要,原始新闻ID,原始新闻标题,来源,URL,创建时间,更新时间
94,【投资市场】AI应用产品契合年轻人消费，...,1155,【盘中宝】上线即售罄...,财联社,https://...,2026-01-09 12:15:31,2026-01-09 12:15:31
...
```

## 💡 使用技巧

### 1. 在Excel中打开CSV

由于CSV使用UTF-8编码，在Excel中打开时：

**Windows Excel:**
- 数据 → 获取数据 → 从文本/CSV
- 选择文件后，编码选择"UTF-8"

**Mac Excel:**
- 直接打开即可，Excel会自动识别UTF-8

**WPS Office:**
- 数据 → 导入数据 → 选择文件和UTF-8编码

### 2. 使用pandas分析

```python
import pandas as pd

# 读取CSV
df = pd.read_csv('curated_news_simple.csv')

# 查看数据
print(df.head())
print(df.info())

# 统计分类
categories = df['AI精选标题'].str.extract(r'【(.*?)】')[0]
print(categories.value_counts())
```

### 3. 使用命令行工具

```bash
# 查看前10行
head -11 curated_news_simple.csv

# 统计总行数（减去表头）
wc -l curated_news_simple.csv

# 搜索特定关键词
grep "AI" curated_news_simple.csv

# 按分类统计
cut -d',' -f2 curated_news_simple.csv | grep -oP '【\K[^】]+' | sort | uniq -c
```

## 📝 注意事项

1. **文件编码**: 所有CSV文件使用UTF-8 with BOM编码（`utf-8-sig`），确保Excel正确显示中文
2. **数据更新**: 数据库实时更新，每次导出都是最新数据
3. **文件覆盖**: 指定 `--output` 时会覆盖已存在的同名文件
4. **性能**: 导出大量数据（>10000条）可能需要几秒钟

## 🛠️ 故障排查

### 问题1: 提示"数据库文件不存在"

**解决方法:**
```bash
# 检查数据库是否存在
ls -lh data/hotnews.db

# 如果不存在，先运行爬虫生成数据
python3 main.py all
```

### 问题2: Excel打开乱码

**解决方法:**
1. 使用"数据 → 从文本/CSV"导入
2. 或用记事本打开，另存为ANSI编码
3. 推荐使用WPS或LibreOffice

### 问题3: 导出的数据为空

**可能原因:**
- 数据库中没有AI精选新闻数据
- 需要先运行AI分析功能

**解决方法:**
```bash
# 检查数据库
python3 -c "
import sys
sys.path.insert(0, 'src')
from database import DatabaseManager
db = DatabaseManager('data/hotnews.db')
print(f'AI精选新闻数量: {db.get_curated_news_count()}')
"
```

## 📞 技术支持

如有问题，请查看：
- 项目README.md
- 数据库模块文档：src/database.py
- 日志文件：logs/

## 🔄 更新日志

- **v1.0** (2026-01-09)
  - ✅ 初始版本
  - ✅ 支持简化版和详细版导出
  - ✅ 支持自定义输出文件名和数量限制
  - ✅ UTF-8 BOM编码支持
