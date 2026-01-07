#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MMchange.py 作为 Tool 调用验证脚本

该脚本验证 MMchange.py 是否能够作为 LangChain Tool 被调用：
1. 检查 ChangeDetectionFunction 是否正确封装
2. 测试在 RSChatGPT 中的 ChangeDetection 工具
3. 验证 tool 的输入输出格式
4. 测试多种调用场景

使用方法：
python test_mmchange_as_tool.py [--device cuda:0]
"""

import sys
import os
import torch
import traceback

# 添加项目路径
PROJECT_ROOT = "/root/Remote-Sensing-ChatGPT"
sys.path.insert(0, PROJECT_ROOT)

def print_section(title):
    """打印分隔线标题"""
    print("\n" + "=" * 70)
    print(f"  {title}")
    print("=" * 70)

def test_change_detection_function():
    """测试 ChangeDetectionFunction 是否可以导入"""
    print_section("步骤 1: 测试 ChangeDetectionFunction 导入")
    
    try:
        from RStask import ChangeDetectionFunction
        print(f"  ✓ ChangeDetectionFunction 导入成功")
        return True, ChangeDetectionFunction
    except Exception as e:
        print(f"  ✗ ChangeDetectionFunction 导入失败:")
        print(f"    {e}")
        traceback.print_exc()
        return False, None

def test_change_detection_function_init(ChangeDetectionFunction, device='cuda:0'):
    """测试 ChangeDetectionFunction 初始化"""
    print_section(f"步骤 2: 测试 ChangeDetectionFunction 初始化 (设备: {device})")
    
    # 如果是 cuda 设备，检查是否可用
    if 'cuda' in device:
        if not torch.cuda.is_available():
            print(f"  ⚠ CUDA 不可用，切换到 CPU")
            device = 'cpu'
        else:
            print(f"  ✓ CUDA 可用")
    
    try:
        func = ChangeDetectionFunction(device)
        print(f"  ✓ ChangeDetectionFunction 初始化成功")
        print(f"  ✓ 类型: {type(func)}")
        
        # 检查是否有 inference 方法
        if hasattr(func, 'inference'):
            print(f"  ✓ inference 方法存在")
        else:
            print(f"  ✗ inference 方法不存在")
            return False, None
        
        return True, func
    except Exception as e:
        print(f"  ✗ ChangeDetectionFunction 初始化失败:")
        print(f"    {e}")
        traceback.print_exc()
        return False, None

def test_change_detection_tool_wrapper(device='cuda:0'):
    """测试 RSChatGPT 中的 ChangeDetection 工具封装"""
    print_section(f"步骤 3: 测试 ChangeDetection 工具封装")
    
    try:
        # 导入 RSChatGPT-shell 中的 ChangeDetection 类
        # 由于文件名包含连字符，需要使用 importlib
        import importlib.util
        spec = importlib.util.spec_from_file_location(
            "RSChatGPT_shell", 
            "/root/Remote-Sensing-ChatGPT/RSChatGPT-shell.py"
        )
        RSChatGPT_shell = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(RSChatGPT_shell)
        ChangeDetection = RSChatGPT_shell.ChangeDetection
        print(f"  ✓ ChangeDetection 工具类导入成功")
        
        # 初始化工具
        if 'cuda' in device and not torch.cuda.is_available():
            device = 'cpu'
            print(f"  ⚠ CUDA 不可用，使用 CPU")
        
        tool = ChangeDetection(device)
        print(f"  ✓ ChangeDetection 工具初始化成功")
        
        # 检查工具属性
        if hasattr(tool, 'inference'):
            print(f"  ✓ inference 方法存在")
        else:
            print(f"  ✗ inference 方法不存在")
            return False, None
        
        # 检查 prompts 装饰器设置的属性
        if hasattr(tool.inference, 'name'):
            print(f"  ✓ 工具名称: {tool.inference.name}")
        else:
            print(f"  ⚠ 工具名称未设置")
        
        if hasattr(tool.inference, 'description'):
            print(f"  ✓ 工具描述: {tool.inference.description[:100]}...")
        else:
            print(f"  ⚠ 工具描述未设置")
        
        return True, tool
    except Exception as e:
        print(f"  ✗ ChangeDetection 工具封装测试失败:")
        print(f"    {e}")
        traceback.print_exc()
        return False, None

def create_test_images():
    """创建测试图像"""
    from PIL import Image
    import numpy as np
    
    test_dir = "/root/Remote-Sensing-ChatGPT/test_images"
    os.makedirs(test_dir, exist_ok=True)
    
    pre_image_path = os.path.join(test_dir, "test_pre.png")
    post_image_path = os.path.join(test_dir, "test_post.png")
    
    # 如果测试图像已存在，直接使用
    if os.path.exists(pre_image_path) and os.path.exists(post_image_path):
        return pre_image_path, post_image_path
    
    # 创建测试图像
    # 前时相：绿色背景
    pre_img = np.ones((256, 256, 3), dtype=np.uint8) * [50, 150, 50]
    np.random.seed(42)
    noise = np.random.randint(-20, 20, (256, 256, 3))
    pre_img = np.clip(pre_img + noise, 0, 255).astype(np.uint8)
    
    # 后时相：添加建筑物
    post_img = pre_img.copy()
    post_img[50:100, 50:150] = [150, 150, 150]
    post_img[120:200, 180:230] = [140, 140, 140]
    
    Image.fromarray(pre_img).save(pre_image_path)
    Image.fromarray(post_img).save(post_image_path)
    
    return pre_image_path, post_image_path

def test_tool_inference(tool, pre_image_path, post_image_path):
    """测试工具推理"""
    print_section("步骤 4: 测试工具推理功能")
    
    # 测试场景
    test_cases = [
        {
            'name': '场景 1: 基本变化检测（两个图像）',
            'inputs': f'{pre_image_path},{post_image_path}',
        },
        {
            'name': '场景 2: 带变化描述的检测',
            'inputs': f'{pre_image_path},{post_image_path},buildings have been constructed',
        },
    ]
    
    results = {}
    
    for test_case in test_cases:
        print(f"\n  {test_case['name']}")
        print(f"  输入: {test_case['inputs']}")
        print()
        
        try:
            result = tool.inference(test_case['inputs'])
            print(f"  ✓ 调用成功")
            print(f"  输出: {result}")
            
            # 检查输出格式
            if 'Output:' in result and '.png' in result:
                print(f"  ✓ 输出格式正确（包含输出文件路径）")
                results[test_case['name']] = True
            else:
                print(f"  ⚠ 输出格式可能不完整")
                results[test_case['name']] = True
                
        except Exception as e:
            print(f"  ✗ 调用失败:")
            print(f"    {e}")
            traceback.print_exc()
            results[test_case['name']] = False
    
    return results

def test_tool_error_handling(tool):
    """测试工具错误处理"""
    print_section("步骤 5: 测试工具错误处理")
    
    error_cases = [
        {
            'name': '错误输入 1: 只提供一个图像',
            'inputs': 'single_image.png',
            'should_fail': True
        },
        {
            'name': '错误输入 2: 空字符串',
            'inputs': '',
            'should_fail': True
        },
        {
            'name': '错误输入 3: 不存在的文件',
            'inputs': 'nonexistent1.png,nonexistent2.png',
            'should_fail': True
        },
    ]
    
    results = {}
    
    for error_case in error_cases:
        print(f"\n  {error_case['name']}")
        print(f"  输入: '{error_case['inputs']}'")
        
        try:
            result = tool.inference(error_case['inputs'])
            
            if error_case['should_fail']:
                # 期望失败但成功了
                if 'Error' in result or 'error' in result.lower():
                    print(f"  ✓ 正确处理错误（返回错误信息）")
                    print(f"  错误信息: {result}")
                    results[error_case['name']] = True
                else:
                    print(f"  ⚠ 未正确处理错误（应该返回错误信息）")
                    print(f"  返回: {result}")
                    results[error_case['name']] = False
            else:
                print(f"  ✓ 调用成功")
                results[error_case['name']] = True
                
        except Exception as e:
            if error_case['should_fail']:
                print(f"  ✓ 正确抛出异常")
                print(f"  异常: {type(e).__name__}: {e}")
                results[error_case['name']] = True
            else:
                print(f"  ✗ 意外异常:")
                print(f"    {e}")
                results[error_case['name']] = False
    
    return results

def test_langchain_tool_integration(device='cuda:0'):
    """测试与 LangChain Tool 的集成"""
    print_section("步骤 6: 测试 LangChain Tool 集成")
    
    try:
        from langchain.agents.tools import Tool
        
        # 导入 ChangeDetection（使用 importlib 处理连字符文件名）
        import importlib.util
        spec = importlib.util.spec_from_file_location(
            "RSChatGPT_shell", 
            "/root/Remote-Sensing-ChatGPT/RSChatGPT-shell.py"
        )
        RSChatGPT_shell = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(RSChatGPT_shell)
        ChangeDetection = RSChatGPT_shell.ChangeDetection
        
        # 创建 ChangeDetection 实例
        if 'cuda' in device and not torch.cuda.is_available():
            device = 'cpu'
        
        change_detection = ChangeDetection(device)
        
        # 创建 LangChain Tool
        tool = Tool(
            name=change_detection.inference.name if hasattr(change_detection.inference, 'name') else "Change Detection",
            func=change_detection.inference,
            description=change_detection.inference.description if hasattr(change_detection.inference, 'description') else "Change detection tool"
        )
        
        print(f"  ✓ LangChain Tool 创建成功")
        print(f"  工具名称: {tool.name}")
        print(f"  工具描述: {tool.description[:100]}...")
        
        # 测试 tool 调用
        pre_img, post_img = create_test_images()
        test_input = f"{pre_img},{post_img}"
        
        print(f"\n  测试 Tool 调用...")
        print(f"  输入: {test_input}")
        
        result = tool.run(test_input)
        print(f"  ✓ Tool 调用成功")
        print(f"  结果: {result[:200]}...")
        
        return True
        
    except Exception as e:
        print(f"  ✗ LangChain Tool 集成测试失败:")
        print(f"    {e}")
        traceback.print_exc()
        return False

def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description='MMchange.py 作为 Tool 调用验证')
    parser.add_argument('--device', type=str, default='cuda:0',
                       choices=['cuda:0', 'cuda:1', 'cpu'],
                       help='设备类型')
    parser.add_argument('--skip_langchain', action='store_true',
                       help='跳过 LangChain 集成测试')
    
    args = parser.parse_args()
    
    print("\n")
    print("╔" + "═" * 68 + "╗")
    print("║" + " " * 13 + "MMchange.py 作为 Tool 调用验证" + " " * 24 + "║")
    print("╚" + "═" * 68 + "╝")
    
    # 记录测试结果
    test_results = {}
    
    # 1. 测试 ChangeDetectionFunction 导入
    success, ChangeDetectionFunction = test_change_detection_function()
    test_results['ChangeDetectionFunction 导入'] = success
    if not success:
        print("\n❌ ChangeDetectionFunction 导入失败")
        return False
    
    # 2. 测试 ChangeDetectionFunction 初始化
    success, func = test_change_detection_function_init(ChangeDetectionFunction, args.device)
    test_results['ChangeDetectionFunction 初始化'] = success
    if not success:
        print("\n❌ ChangeDetectionFunction 初始化失败")
        return False
    
    # 3. 测试 ChangeDetection 工具封装
    success, tool = test_change_detection_tool_wrapper(args.device)
    test_results['ChangeDetection 工具封装'] = success
    if not success:
        print("\n❌ ChangeDetection 工具封装失败")
        return False
    
    # 4. 准备测试图像
    print_section("准备测试图像")
    pre_image_path, post_image_path = create_test_images()
    print(f"  ✓ 测试图像准备完成")
    print(f"    前时相: {pre_image_path}")
    print(f"    后时相: {post_image_path}")
    
    # 5. 测试工具推理
    inference_results = test_tool_inference(tool, pre_image_path, post_image_path)
    test_results.update(inference_results)
    
    # 6. 测试错误处理
    error_results = test_tool_error_handling(tool)
    test_results.update(error_results)
    
    # 7. 测试 LangChain Tool 集成（可选）
    if not args.skip_langchain:
        langchain_success = test_langchain_tool_integration(args.device)
        test_results['LangChain Tool 集成'] = langchain_success
    
    # 总结
    print_section("验证结果总结")
    
    all_passed = True
    for test_name, result in test_results.items():
        status = "✓ 通过" if result else "✗ 失败"
        print(f"  {test_name:40s}: {status}")
        if not result:
            all_passed = False
    
    print("\n" + "=" * 70)
    if all_passed:
        print("  🎉 所有测试通过！MMchange.py 可以作为 Tool 调用")
    else:
        print("  ❌ 部分测试失败，请检查上述错误信息")
    print("=" * 70 + "\n")
    
    return all_passed

if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)

