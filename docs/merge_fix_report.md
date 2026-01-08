# AI精选新闻合并功能修复报告

## 问题描述

在AI精选新闻合并功能中,发现以下问题:
- 当AI精选新闻被合并后,原始的新闻记录仍然存在于 `news` 表中
- 这导致数据重复,原始新闻和合并后的AI精选新闻都指向同一条新闻内容
- 应该在合并时删除 `news` 表中对应的原始新闻记录

## 修复方案

### 1. 修改数据库合并逻辑

**文件**: [src/database.py](src/database.py)

在 `merge_curated_news` 方法中添加了自动删除原始新闻的功能:

```python
# 2. 获取要合并记录的source_news_id（用于删除原始新闻）
placeholders = ','.join('?' * len(merge_ids))
cursor = conn.execute(f"""
    SELECT source_news_id
    FROM curated_news
    WHERE id IN ({placeholders})
""", merge_ids)
source_news_ids_to_delete = [row[0] for row in cursor.fetchall() if row[0]]

# ... 更新curated_news表 ...

# 5. 删除news表中的原始新闻记录（避免重复）
if source_news_ids_to_delete:
    delete_placeholders = ','.join('?' * len(source_news_ids_to_delete))
    cursor = conn.execute(f"""
        DELETE FROM news
        WHERE id IN ({delete_placeholders})
    """, source_news_ids_to_delete)
    deleted_count = cursor.rowcount
    self.logger.info(f"合并新闻时删除了 {deleted_count} 条原始新闻记录: {source_news_ids_to_delete}")
```

### 2. 创建历史数据清理脚本

**文件**: [cleanup_merged_news.py](cleanup_merged_news.py)

用于清理历史遗留的已合并原始新闻记录。

**功能**:
- 查找所有被合并的AI精选新闻 (is_merged=1)
- 检查对应的原始新闻是否还在news表中
- 提供试运行模式 (默认)
- 支持实际删除模式 (--execute)

**使用方法**:

```bash
# 查看统计信息
python3 cleanup_merged_news.py --stats

# 试运行(查看会被删除的记录)
python3 cleanup_merged_news.py

# 实际执行删除
python3 cleanup_merged_news.py --execute
```

### 3. 创建测试脚本

**文件**: [test_merge_fix.py](test_merge_fix.py)

自动化测试脚本,验证修复后的合并功能。

**测试内容**:
1. 插入测试新闻数据
2. 创建AI精选新闻
3. 执行合并操作
4. 验证原始新闻是否被正确删除

**运行测试**:

```bash
python3 test_merge_fix.py
```

## 修复验证

### 测试结果

```
=== 步骤6: 验证结果 ===
✓ 测试通过: 原始新闻已被正确删除
  - 合并前: 4 条
  - 预期删除: 3 条
  - 合并后: 1 条
```

### 合并逻辑说明

修复后的合并流程:

1. **更新保留记录**: 更新主记录的标题、摘要和合并来源列表
2. **标记被合并记录**: 将被合并的记录标记为 is_merged=1
3. **删除原始新闻**: 自动删除 `news` 表中对应的原始新闻记录
4. **记录日志**: 记录删除的原始新闻ID和数量

## 数据库影响

### 修复前的问题

```
news表:
  - ID=217: 比亚迪终结特斯拉时代...
  - ID=218: 多家车企公布2026销量目标...  ← 应该被删除
  - ID=219: 蔚来不飘了...                 ← 应该被删除
  - ID=220: 宝马开年挥刀...               ← 应该被删除

curated_news表:
  - ID=8: 合并后的新闻 (merged_from=[9,10,11])
  - ID=9: 已合并 (is_merged=1, source_news_id=218)
  - ID=10: 已合并 (is_merged=1, source_news_id=219)
  - ID=11: 已合并 (is_merged=1, source_news_id=220)
```

### 修复后的效果

```
news表:
  - ID=217: 比亚迪终结特斯拉时代...  ← 保留
  ← ID 218,219,220 已被删除

curated_news表:
  - ID=8: 合并后的新闻 (merged_from=[9,10,11])
  - ID=9: 已合并 (is_merged=1, source_news_id=218)
  - ID=10: 已合并 (is_merged=1, source_news_id=219)
  - ID=11: 已合并 (is_merged=1, source_news_id=220)
```

## 使用建议

### 1. 对于现有数据库

如果数据库中已经有历史合并记录,建议运行清理脚本:

```bash
# 先试运行查看影响
python3 cleanup_merged_news.py

# 确认无误后执行
python3 cleanup_merged_news.py --execute
```

### 2. 对于未来的合并操作

修复后的合并逻辑会自动删除原始新闻,无需手动干预。

### 3. 数据备份

在执行清理操作前,建议备份数据库:

```bash
cp data/hotnews.db data/hotnews.db.backup
```

## 相关文件

- [src/database.py:841-913](src/database.py#L841-L913) - 修复后的合并方法
- [cleanup_merged_news.py](cleanup_merged_news.py) - 历史数据清理脚本
- [test_merge_fix.py](test_merge_fix.py) - 测试脚本

## 总结

此次修复解决了AI精选新闻合并功能中的数据重复问题,确保:
- ✅ 合并时自动删除原始新闻记录
- ✅ 避免数据重复
- ✅ 保持数据一致性
- ✅ 提供清理工具处理历史数据
- ✅ 通过自动化测试验证功能正确性
