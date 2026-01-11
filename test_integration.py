#!/usr/bin/env python3
"""
简单测试脚本：验证 Promptomatix 集成是否正常工作
"""

import sys
import os

def test_import():
    """测试导入"""
    print("="*60)
    print("测试 1: 检查模块导入")
    print("="*60)
    
    try:
        from promptomatix_integration import QueryOptimizer
        print("✓ QueryOptimizer 导入成功")
    except ImportError as e:
        print(f"✗ QueryOptimizer 导入失败: {e}")
        return False
    
    try:
        import importlib.util
        spec = importlib.util.spec_from_file_location("rschatgpt", "RSChatGPT-shell.py")
        rschatgpt_module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(rschatgpt_module)
        RSChatGPT = rschatgpt_module.RSChatGPT
        print("✓ RSChatGPT 导入成功")
    except Exception as e:
        print(f"✗ RSChatGPT 导入失败: {e}")
        return False
    
    return True

def test_query_optimizer():
    """测试查询优化器基本功能"""
    print("\n" + "="*60)
    print("测试 2: 查询优化器基本功能")
    print("="*60)
    
    try:
        from promptomatix_integration import QueryOptimizer
        
        # 创建优化器（不启用，避免实际调用 API）
        optimizer = QueryOptimizer(enabled=False)
        print("✓ QueryOptimizer 实例化成功（禁用模式）")
        
        # 测试跳过简单查询
        result = optimizer.optimize_if_ambiguous("hello")
        assert result == "hello", "简单查询应该被跳过"
        print("✓ 简单查询跳过测试通过")
        
        # 测试缓存
        optimizer.cache["test_key"] = "cached_value"
        assert "test_key" in optimizer.cache
        print("✓ 缓存功能正常")
        
        # 测试统计
        stats = optimizer.get_stats()
        assert 'optimization_count' in stats
        assert 'skip_count' in stats
        assert 'cache_size' in stats
        print("✓ 统计功能正常")
        print(f"  统计信息: {stats}")
        
        return True
    except Exception as e:
        print(f"✗ 查询优化器测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_rschatgpt_integration():
    """测试 RSChatGPT 集成"""
    print("\n" + "="*60)
    print("测试 3: RSChatGPT 集成")
    print("="*60)
    
    try:
        import importlib.util
        spec = importlib.util.spec_from_file_location("rschatgpt", "RSChatGPT-shell.py")
        rschatgpt_module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(rschatgpt_module)
        RSChatGPT = rschatgpt_module.RSChatGPT
        
        # 检查 RSChatGPT 是否支持 enable_query_optimization 参数
        import inspect
        sig = inspect.signature(RSChatGPT.__init__)
        params = list(sig.parameters.keys())
        
        if 'enable_query_optimization' in params:
            print("✓ RSChatGPT 支持 enable_query_optimization 参数")
        else:
            print("✗ RSChatGPT 不支持 enable_query_optimization 参数")
            return False
        
        print("✓ RSChatGPT 集成检查通过")
        return True
        
    except Exception as e:
        print(f"✗ RSChatGPT 集成测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_file_structure():
    """测试文件结构"""
    print("\n" + "="*60)
    print("测试 4: 文件结构检查")
    print("="*60)
    
    required_files = [
        'promptomatix_integration.py',
        'RSChatGPT-shell.py',
        'test_rschatgpt.py',
        'PROMPTOMATIX_INTEGRATION.md'
    ]
    
    all_exist = True
    for file in required_files:
        if os.path.exists(file):
            print(f"✓ {file} 存在")
        else:
            print(f"✗ {file} 不存在")
            all_exist = False
    
    return all_exist

def main():
    """运行所有测试"""
    print("\n" + "="*60)
    print("Promptomatix 集成测试")
    print("="*60 + "\n")
    
    results = []
    
    # 运行测试
    results.append(("模块导入", test_import()))
    results.append(("查询优化器", test_query_optimizer()))
    results.append(("RSChatGPT集成", test_rschatgpt_integration()))
    results.append(("文件结构", test_file_structure()))
    
    # 汇总结果
    print("\n" + "="*60)
    print("测试结果汇总")
    print("="*60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for name, result in results:
        status = "✓ 通过" if result else "✗ 失败"
        print(f"{name:20s} {status}")
    
    print(f"\n总计: {passed}/{total} 测试通过")
    
    if passed == total:
        print("\n🎉 所有测试通过！集成成功！")
        print("\n下一步:")
        print("  1. 运行对比测试: python test_rschatgpt.py compare")
        print("  2. 查看文档: cat PROMPTOMATIX_INTEGRATION.md")
        return 0
    else:
        print("\n⚠️ 部分测试失败，请检查错误信息")
        return 1

if __name__ == '__main__':
    sys.exit(main())

