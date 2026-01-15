#!/usr/bin/env python3
"""
从完整的QA数据集中均匀抽取指定比例的样本
"""

import json
import sys
import os

def create_sampled_qa(input_file, output_file, sample_ratio=0.2):
    """
    从完整QA数据集中均匀抽取样本
    
    Args:
        input_file: 输入的完整QA JSON文件
        output_file: 输出的采样QA JSON文件
        sample_ratio: 采样比例 (0-1之间)
    """
    print(f"正在读取文件: {input_file}")
    
    with open(input_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    total_samples = len(data)
    sample_size = int(total_samples * sample_ratio)
    
    print(f"总样本数: {total_samples}")
    print(f"采样比例: {sample_ratio * 100:.1f}%")
    print(f"采样数量: {sample_size}")
    
    # 均匀采样 - 计算采样间隔
    step = total_samples / sample_size
    
    sampled_data = []
    sampled_indices = []
    
    for i in range(sample_size):
        idx = int(i * step)
        sampled_data.append(data[idx])
        sampled_indices.append(idx)
    
    print(f"\n采样索引示例 (前10个): {sampled_indices[:10]}")
    print(f"采样索引示例 (后10个): {sampled_indices[-10:]}")
    
    # 保存采样数据
    print(f"\n正在保存到: {output_file}")
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(sampled_data, f, ensure_ascii=False, indent=2)
    
    print(f"✓ 采样完成！")
    
    # 统计各工具的分布
    tool_distribution = {}
    for sample in sampled_data:
        tool = sample.get('tool', 'Unknown')
        tool_distribution[tool] = tool_distribution.get(tool, 0) + 1
    
    print(f"\n采样后的工具分布:")
    print(f"{'工具名称':<30} {'样本数':<10} {'占比':<10}")
    print("-" * 50)
    for tool, count in sorted(tool_distribution.items(), key=lambda x: -x[1]):
        ratio = count / sample_size * 100
        print(f"{tool:<30} {count:<10} {ratio:.2f}%")
    
    return sampled_data, sampled_indices

def main():
    """主函数"""
    if len(sys.argv) < 2:
        print("用法: python create_sampled_qa.py <input_file> [sample_ratio] [output_file]")
        print("\n示例:")
        print("  python create_sampled_qa.py QAjsons/singleturn_qa_152.json")
        print("  python create_sampled_qa.py QAjsons/singleturn_qa_152.json 0.2")
        print("  python create_sampled_qa.py QAjsons/singleturn_qa_152.json 0.2 QAjsons/singleturn_qa_152_20pct.json")
        sys.exit(1)
    
    input_file = sys.argv[1]
    sample_ratio = float(sys.argv[2]) if len(sys.argv) > 2 else 0.2
    
    # 自动生成输出文件名
    if len(sys.argv) > 3:
        output_file = sys.argv[3]
    else:
        base_name = os.path.splitext(input_file)[0]
        pct = int(sample_ratio * 100)
        output_file = f"{base_name}_{pct}pct.json"
    
    try:
        sampled_data, sampled_indices = create_sampled_qa(input_file, output_file, sample_ratio)
        
        # 保存采样索引
        indices_file = output_file.replace('.json', '_indices.json')
        with open(indices_file, 'w', encoding='utf-8') as f:
            json.dump({
                'total_samples': len(sampled_data),
                'sample_ratio': sample_ratio,
                'indices': sampled_indices
            }, f, ensure_ascii=False, indent=2)
        
        print(f"\n✓ 采样索引已保存到: {indices_file}")
        print(f"\n完成！采样数据已保存到: {output_file}")
        
    except Exception as e:
        print(f"错误: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == '__main__':
    main()

