#!/usr/bin/env python3
"""
简单测试：验证优化器是否真的工作
"""
from promptomatix_integration import QueryOptimizer

# 创建优化器
optimizer = QueryOptimizer(
    model_name="gpt-3.5-turbo",
    openai_key="sk-SPp8PGpzob5k1pcSI2cRORgdeEDoB3QsndvRzIYnUVeKt2jd",
    proxy_url="https://api.chatanywhere.tech",
    enabled=True
)

print("="*60)
print("测试查询优化器")
print("="*60)

# 测试几个查询
test_queries = [
    "这图里有啥",
    "你能帮我看看这是哪拍的吗？",
    "这个地方最近有什么新东西没？",
    "麻烦分别告诉我这两张图都拍了啥？",
    "这张图的清晰度怎么样？"
]

for i, query in enumerate(test_queries, 1):
    print(f"\n[测试 {i}]")
    print(f"原始查询: {query}")
    result = optimizer.optimize_if_ambiguous(query)
    print(f"优化结果: {result}")
    print(f"是否优化: {'是' if result != query else '否'}")

# 显示统计
print("\n" + "="*60)
print("统计结果")
print("="*60)
stats = optimizer.get_stats()
print(f"优化次数: {stats['optimization_count']}")
print(f"跳过次数: {stats['skip_count']}")
print(f"缓存大小: {stats['cache_size']}")
print("="*60)



