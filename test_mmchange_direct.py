#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MMchange.py 直接运行验证脚本

该脚本验证 MMchange.py 是否能够：
1. 成功导入所有依赖
2. 正确初始化模型
3. 执行变化检测推理
4. 生成可视化结果

使用方法：
python test_mmchange_direct.py [--device cuda:0]
"""

import sys
import os
import torch
import traceback
from pathlib import Path

# 添加项目路径
PROJECT_ROOT = "/root/Remote-Sensing-ChatGPT"
sys.path.insert(0, PROJECT_ROOT)

def print_section(title):
    """打印分隔线标题"""
    print("\n" + "=" * 70)
    print(f"  {title}")
    print("=" * 70)

def check_dependencies():
    """检查依赖是否可用"""
    print_section("步骤 1: 检查依赖")
    
    dependencies = {
        'torch': 'PyTorch',
        'PIL': 'Pillow',
        'clip': 'CLIP',
        'cv2': 'OpenCV',
        'numpy': 'NumPy',
    }
    
    all_good = True
    for module_name, display_name in dependencies.items():
        try:
            __import__(module_name)
            print(f"  ✓ {display_name} ({module_name})")
        except ImportError as e:
            print(f"  ✗ {display_name} ({module_name}) - 未安装或无法导入")
            print(f"    错误: {e}")
            all_good = False
    
    return all_good

def check_model_file():
    """检查模型文件是否存在"""
    print_section("步骤 2: 检查模型文件")
    
    model_path = '/root/MMchange-main/results_change_caption_transfer_LEVIR_iter_40000_lr_0.0005/best_model.pth'
    
    if os.path.exists(model_path):
        file_size = os.path.getsize(model_path) / (1024 * 1024)  # MB
        print(f"  ✓ 模型文件存在: {model_path}")
        print(f"  ✓ 文件大小: {file_size:.2f} MB")
        return True
    else:
        print(f"  ✗ 模型文件不存在: {model_path}")
        return False

def check_mmchange_modules():
    """检查 MMchange 相关模块是否可导入"""
    print_section("步骤 3: 检查 MMchange 模块")
    
    all_good = True
    
    # 检查 Transforms
    try:
        MMCHANGE_PATH = '/root/MMchange-main'
        sys.path.insert(0, MMCHANGE_PATH)
        import Transforms as myTransforms
        print(f"  ✓ Transforms 模块导入成功")
    except Exception as e:
        print(f"  ✗ Transforms 模块导入失败: {e}")
        all_good = False
    
    # 检查 model 模块
    try:
        from models.model import BaseNet, BaseNet_Hybrid
        print(f"  ✓ models.model 模块导入成功")
    except Exception as e:
        print(f"  ✗ models.model 模块导入失败: {e}")
        all_good = False
    
    return all_good

def test_mmchange_import():
    """测试 MMchange 类是否可以导入"""
    print_section("步骤 4: 测试 MMChangeDetection 类导入")
    
    try:
        from RStask.ChangeDetection.MMchange import MMChangeDetection
        print(f"  ✓ MMChangeDetection 类导入成功")
        return True, MMChangeDetection
    except Exception as e:
        print(f"  ✗ MMChangeDetection 类导入失败:")
        print(f"    {e}")
        traceback.print_exc()
        return False, None

def test_mmchange_initialization(MMChangeDetection, device='cuda:0'):
    """测试 MMchange 模型初始化"""
    print_section(f"步骤 5: 测试模型初始化 (设备: {device})")
    
    # 如果是 cuda 设备，检查是否可用
    if 'cuda' in device:
        if not torch.cuda.is_available():
            print(f"  ⚠ CUDA 不可用，切换到 CPU")
            device = 'cpu'
        else:
            print(f"  ✓ CUDA 可用")
            print(f"    GPU 设备: {torch.cuda.get_device_name(0)}")
    
    try:
        detector = MMChangeDetection(device=device)
        print(f"  ✓ 模型初始化成功")
        return True, detector
    except Exception as e:
        print(f"  ✗ 模型初始化失败:")
        print(f"    {e}")
        traceback.print_exc()
        return False, None

def create_test_images():
    """创建测试图像（如果没有现成的）"""
    print_section("步骤 6: 准备测试图像")
    
    from PIL import Image
    import numpy as np
    
    test_dir = "/root/Remote-Sensing-ChatGPT/test_images"
    os.makedirs(test_dir, exist_ok=True)
    
    pre_image_path = os.path.join(test_dir, "test_pre.png")
    post_image_path = os.path.join(test_dir, "test_post.png")
    
    # 如果测试图像已存在，直接使用
    if os.path.exists(pre_image_path) and os.path.exists(post_image_path):
        print(f"  ✓ 使用现有测试图像")
        print(f"    前时相: {pre_image_path}")
        print(f"    后时相: {post_image_path}")
        return pre_image_path, post_image_path
    
    # 创建简单的测试图像（256x256 RGB）
    print(f"  ⚠ 未找到测试图像，创建模拟图像...")
    
    # 前时相：绿色背景（模拟植被）
    pre_img = np.ones((256, 256, 3), dtype=np.uint8) * [50, 150, 50]
    # 添加一些纹理
    np.random.seed(42)
    noise = np.random.randint(-20, 20, (256, 256, 3))
    pre_img = np.clip(pre_img + noise, 0, 255).astype(np.uint8)
    
    # 后时相：在某些区域添加建筑物（灰色）
    post_img = pre_img.copy()
    # 添加一些"建筑物"（灰色矩形）
    post_img[50:100, 50:150] = [150, 150, 150]
    post_img[120:200, 180:230] = [140, 140, 140]
    
    # 保存图像
    Image.fromarray(pre_img).save(pre_image_path)
    Image.fromarray(post_img).save(post_image_path)
    
    print(f"  ✓ 测试图像创建成功")
    print(f"    前时相: {pre_image_path}")
    print(f"    后时相: {post_image_path}")
    
    return pre_image_path, post_image_path

def test_inference(detector, pre_image_path, post_image_path):
    """测试变化检测推理"""
    print_section("步骤 7: 测试变化检测推理")
    
    output_dir = "/root/Remote-Sensing-ChatGPT/test_results"
    os.makedirs(output_dir, exist_ok=True)
    output_path = os.path.join(output_dir, "test_result.png")
    
    print(f"  输入:")
    print(f"    前时相: {pre_image_path}")
    print(f"    后时相: {post_image_path}")
    print(f"  输出:")
    print(f"    结果图像: {output_path}")
    print()
    
    try:
        result_text = detector.inference(
            pre_image_path=pre_image_path,
            post_image_path=post_image_path,
            output_path=output_path,
            change_caption="buildings have been constructed or demolished"
        )
        
        print(f"\n  ✓ 推理执行成功")
        print(f"    {result_text}")
        
        # 检查输出文件是否生成
        if os.path.exists(output_path):
            file_size = os.path.getsize(output_path) / 1024  # KB
            print(f"  ✓ 结果文件已生成")
            print(f"    路径: {output_path}")
            print(f"    大小: {file_size:.2f} KB")
            return True
        else:
            print(f"  ✗ 结果文件未生成")
            return False
            
    except Exception as e:
        print(f"  ✗ 推理执行失败:")
        print(f"    {e}")
        traceback.print_exc()
        return False

def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description='MMchange.py 直接运行验证')
    parser.add_argument('--device', type=str, default='cuda:0',
                       choices=['cuda:0', 'cuda:1', 'cpu'],
                       help='设备类型')
    parser.add_argument('--pre_image', type=str, default=None,
                       help='前时相图像路径（可选，不提供则使用测试图像）')
    parser.add_argument('--post_image', type=str, default=None,
                       help='后时相图像路径（可选，不提供则使用测试图像）')
    
    args = parser.parse_args()
    
    print("\n")
    print("╔" + "═" * 68 + "╗")
    print("║" + " " * 15 + "MMchange.py 直接运行验证" + " " * 29 + "║")
    print("╚" + "═" * 68 + "╝")
    
    # 记录测试结果
    test_results = {}
    
    # 1. 检查依赖
    test_results['dependencies'] = check_dependencies()
    if not test_results['dependencies']:
        print("\n❌ 依赖检查失败，请先安装缺失的依赖")
        return False
    
    # 2. 检查模型文件
    test_results['model_file'] = check_model_file()
    if not test_results['model_file']:
        print("\n❌ 模型文件不存在，请先准备模型文件")
        return False
    
    # 3. 检查 MMchange 模块
    test_results['mmchange_modules'] = check_mmchange_modules()
    if not test_results['mmchange_modules']:
        print("\n❌ MMchange 模块导入失败")
        return False
    
    # 4. 测试 MMChangeDetection 导入
    success, MMChangeDetection = test_mmchange_import()
    test_results['mmchange_import'] = success
    if not success:
        print("\n❌ MMChangeDetection 类导入失败")
        return False
    
    # 5. 测试模型初始化
    success, detector = test_mmchange_initialization(MMChangeDetection, args.device)
    test_results['initialization'] = success
    if not success:
        print("\n❌ 模型初始化失败")
        return False
    
    # 6. 准备测试图像
    if args.pre_image and args.post_image:
        pre_image_path = args.pre_image
        post_image_path = args.post_image
        print_section("步骤 6: 使用指定的测试图像")
        print(f"  前时相: {pre_image_path}")
        print(f"  后时相: {post_image_path}")
    else:
        pre_image_path, post_image_path = create_test_images()
    
    # 7. 测试推理
    test_results['inference'] = test_inference(detector, pre_image_path, post_image_path)
    
    # 总结
    print_section("验证结果总结")
    
    all_passed = True
    for test_name, result in test_results.items():
        status = "✓ 通过" if result else "✗ 失败"
        print(f"  {test_name:20s}: {status}")
        if not result:
            all_passed = False
    
    print("\n" + "=" * 70)
    if all_passed:
        print("  🎉 所有测试通过！MMchange.py 可以直接运行")
    else:
        print("  ❌ 部分测试失败，请检查上述错误信息")
    print("=" * 70 + "\n")
    
    return all_passed

if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)

