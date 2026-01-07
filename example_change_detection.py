"""
ChangeDetection 工具使用示例

演示如何在 RSChatGPT 中使用 ChangeDetection 工具
"""
import os
import argparse
from RSChatGPT_shell import RSChatGPT

def example_standalone():
    """示例 1: 独立使用 ChangeDetection 功能"""
    print("=" * 80)
    print("示例 1: 独立使用 ChangeDetection 功能")
    print("=" * 80)
    
    from RStask import ChangeDetectionFunction
    
    # 初始化模型
    device = "cuda:0"
    cd_func = ChangeDetectionFunction(device)
    
    # 设置测试图像路径
    test_data_dir = "/root/autodl-tmp/datasets/LEVIR-MCI-dataset/images/test"
    pre_image = os.path.join(test_data_dir, "A", "test_000001.png")
    post_image = os.path.join(test_data_dir, "B", "test_000001.png")
    output_path = "/root/Remote-Sensing-ChatGPT/image/change_detection_result.png"
    
    if not os.path.exists(pre_image) or not os.path.exists(post_image):
        print(f"警告: 测试图像不存在，请检查路径")
        print(f"前时相: {pre_image}")
        print(f"后时相: {post_image}")
        return
    
    # 执行变化检测
    print(f"\n前时相图像: {pre_image}")
    print(f"后时相图像: {post_image}")
    print(f"输出路径: {output_path}\n")
    
    result = cd_func.inference(
        pre_image, 
        post_image, 
        output_path,
        change_caption="buildings have been constructed or demolished"
    )
    
    print(f"\n结果: {result}\n")
    print("=" * 80)

def example_with_rschatgpt(openai_key, proxy_url):
    """示例 2: 在 RSChatGPT 对话系统中使用"""
    print("\n" + "=" * 80)
    print("示例 2: 在 RSChatGPT 对话系统中使用")
    print("=" * 80)
    
    # 配置加载的模型
    load_dict = {
        'ImageCaptioning': 'cuda:0',
        'ChangeDetection': 'cuda:0',
        'EdgeDetection': 'cpu'
    }
    
    # 初始化 RSChatGPT
    print("\n正在初始化 RSChatGPT...")
    bot = RSChatGPT(
        gpt_name='gpt-3.5-turbo',
        load_dict=load_dict,
        openai_key=openai_key,
        proxy_url=proxy_url
    )
    bot.initialize()
    print("RSChatGPT 初始化完成！\n")
    
    # 准备测试图像
    test_data_dir = "/root/autodl-tmp/datasets/LEVIR-MCI-dataset/images/test"
    pre_image = os.path.join(test_data_dir, "A", "test_000001.png")
    post_image = os.path.join(test_data_dir, "B", "test_000001.png")
    
    if not os.path.exists(pre_image) or not os.path.exists(post_image):
        print(f"警告: 测试图像不存在")
        return
    
    # 交互示例
    state = []
    
    # 第一步：加载第一张图像
    print("步骤 1: 加载前时相图像")
    state = bot.run_image(pre_image, state, "This is a satellite image from 2018")
    
    # 第二步：请求变化检测
    print("\n步骤 2: 请求变化检测")
    query = f"Compare this image with {post_image} and detect what has changed. " \
            f"Focus on buildings and urban development."
    state = bot.run_text(query, state)
    
    print("\n对话完成！")
    print("=" * 80)

def example_batch_processing():
    """示例 3: 批量处理多对图像"""
    print("\n" + "=" * 80)
    print("示例 3: 批量处理多对图像")
    print("=" * 80)
    
    from RStask import ChangeDetectionFunction
    
    # 初始化模型
    device = "cuda:0"
    cd_func = ChangeDetectionFunction(device)
    
    # 设置数据目录
    test_data_dir = "/root/autodl-tmp/datasets/LEVIR-MCI-dataset/images/test"
    a_dir = os.path.join(test_data_dir, "A")
    b_dir = os.path.join(test_data_dir, "B")
    output_dir = "/root/Remote-Sensing-ChatGPT/image/batch_results"
    
    if not os.path.exists(a_dir) or not os.path.exists(b_dir):
        print(f"警告: 数据目录不存在")
        return
    
    # 创建输出目录
    os.makedirs(output_dir, exist_ok=True)
    
    # 获取图像列表
    a_files = sorted([f for f in os.listdir(a_dir) if f.endswith('.png')])
    b_files = sorted([f for f in os.listdir(b_dir) if f.endswith('.png')])
    
    # 只处理前 3 对图像作为示例
    max_samples = min(3, len(a_files), len(b_files))
    
    print(f"\n将处理 {max_samples} 对图像\n")
    
    for i in range(max_samples):
        pre_image = os.path.join(a_dir, a_files[i])
        post_image = os.path.join(b_dir, b_files[i])
        output_path = os.path.join(output_dir, f"result_{i+1:03d}.png")
        
        print(f"处理第 {i+1}/{max_samples} 对图像...")
        print(f"  前时相: {a_files[i]}")
        print(f"  后时相: {b_files[i]}")
        
        try:
            result = cd_func.inference(
                pre_image,
                post_image,
                output_path,
                change_caption="detect urban development and land use changes"
            )
            print(f"  ✓ {result}")
        except Exception as e:
            print(f"  ✗ 处理失败: {e}")
        
        print()
    
    print(f"批量处理完成！结果保存在: {output_dir}")
    print("=" * 80)

def main():
    parser = argparse.ArgumentParser(description='ChangeDetection 工具使用示例')
    parser.add_argument('--mode', type=str, default='standalone',
                        choices=['standalone', 'rschatgpt', 'batch'],
                        help='运行模式: standalone(独立), rschatgpt(对话系统), batch(批处理)')
    parser.add_argument('--openai_key', type=str, 
                        default="sk-kQ11Ptt3RYbeTj7zBVSADbqXth7mA7Jj5dEmaWgtYiO04zdu",
                        help='OpenAI API key (仅 rschatgpt 模式需要)')
    parser.add_argument('--proxy_url', type=str, 
                        default="https://api.chatanywhere.tech",
                        help='API proxy URL (仅 rschatgpt 模式需要)')
    
    args = parser.parse_args()
    
    print("\n" + "=" * 80)
    print("ChangeDetection 工具使用示例")
    print("=" * 80)
    
    if args.mode == 'standalone':
        example_standalone()
    elif args.mode == 'rschatgpt':
        example_with_rschatgpt(args.openai_key, args.proxy_url)
    elif args.mode == 'batch':
        example_batch_processing()
    
    print("\n示例运行完成！")

if __name__ == '__main__':
    main()

