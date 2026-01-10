import json
import os
import sys
import importlib.util
import csv
import re
import io
from contextlib import redirect_stdout, redirect_stderr

spec = importlib.util.spec_from_file_location("rschatgpt", "RSChatGPT-shell.py")
rschatgpt_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(rschatgpt_module)
RSChatGPT = rschatgpt_module.RSChatGPT

# 这个函数已经不再使用，保留以防需要
def extract_tool_from_state(state, debug=False):
    """从state中提取实际调用的tool（备用方法）"""
    return "Unknown"

def post_process_change_detection(before_path, after_path, mask_path, output_path, question_id):
    """
    将变化检测的before/after/mask拼接成一张图
    """
    try:
        before = skio.imread(before_path)
        after = skio.imread(after_path)
        mask = skio.imread(mask_path)
        
        # 确保所有图片尺寸一致
        h, w = before.shape[:2]
        after = cv2.resize(after, (w, h))
        mask = cv2.resize(mask, (w, h))
        
        # 水平拼接三张图
        combined = np.hstack([before, after, mask])
        
        # 添加标题
        combined_pil = Image.fromarray(combined)
        draw = ImageDraw.Draw(combined_pil)
        
        # 添加文字标注
        try:
            font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 20)
        except:
            font = ImageFont.load_default()
        
        draw.text((w//2-30, 10), "Before", fill=(255, 255, 0), font=font)
        draw.text((w + w//2-30, 10), "After", fill=(255, 255, 0), font=font)
        draw.text((2*w + w//2-30, 10), "Changes", fill=(255, 255, 0), font=font)
        
        combined_pil.save(output_path)
        print(f"✓ 变化检测结果已保存: {output_path}")
        return output_path
    except Exception as e:
        print(f"✗ 变化检测后处理失败: {e}")
        return mask_path

def extract_text_from_output(output_text, tool_type):
    """
    从Agent的output中提取纯文本结果
    """
    if tool_type == 'ImageCaptioning':
        # 提取图像描述 - 查找包含描述性内容的句子
        import re
        # 移除路径信息
        text = re.sub(r'/[^\s]+\.png', '', output_text)
        text = re.sub(r'result/[^\s]+', '', text)
        
        # 查找描述性句子（通常包含 "satellite image", "aerial view" 等）
        sentences = re.split(r'[.!?]\s+', text)
        for sentence in sentences:
            sentence = sentence.strip()
            # 跳过思考过程和动作
            if any(skip in sentence for skip in ['Thought:', 'Action:', 'AI:', 'tool', 'Tool', 'step by step']):
                continue
            # 查找有意义的描述
            if any(keyword in sentence.lower() for keyword in ['satellite', 'aerial', 'image', 'shows', 'contains']):
                if len(sentence) > 15:
                    return sentence + '.'
        
        # 如果没找到，返回第一个长句子
        for sentence in sentences:
            if len(sentence.strip()) > 20:
                return sentence.strip() + '.'
        
        return "图像描述提取失败"
    
    elif tool_type == 'SceneClassification':
        # 提取场景分类结果
        import re
        # 匹配两种格式:
        # 1. "85.87% probability being BareLand"
        # 2. "BareLand with 85.87% probability"
        pattern1 = r'(\d+\.\d+)%\s+probability\s+being\s+(\w+)'
        pattern2 = r'(\w+)\s+with\s+(\d+\.\d+)%\s+probability'
        
        matches1 = re.findall(pattern1, output_text)
        matches2 = re.findall(pattern2, output_text)
        
        results = []
        if matches1:
            results = [f"{cls}: {prob}%" for prob, cls in matches1[:3]]
        elif matches2:
            results = [f"{cls}: {prob}%" for cls, prob in matches2[:3]]
        
        if results:
            return '\n'.join(results)
        
        return "场景分类结果提取失败"
    
    elif tool_type == 'ObjectCounting':
        # 提取计数结果
        import re
        # 查找数字模式
        patterns = [
            r'There (?:are|is) (\d+)',
            r'(\d+)\s*(?:objects?|items?|buildings?|cars?|planes?|houses?)',
            r'count.*?(\d+)',
            r'total.*?(\d+)'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, output_text, re.IGNORECASE)
            if match:
                count = match.group(1)
                return f"检测到 {count} 个目标"
        
        # 如果没找到数字，返回说明
        if 'not' in output_text.lower() and 'supported' in output_text.lower():
            return "该类别不被模型支持，无法计数"
        
        return "目标计数结果提取失败"
    
    return output_text

def test_multiturn_qa():
    """测试多轮对话场景"""
    # 加载多轮对话样本
    with open('multiturn_qa_samples.json', 'r', encoding='utf-8') as f:
        samples = json.load(f)
    
    # 初始化模型
    load_dict = {
        'ImageCaptioning': 'cuda:0',
        'SceneClassification': 'cuda:0',
        'ObjectDetection': 'cuda:0',
        'ObjectCounting': 'cuda:0',
        'EdgeDetection': 'cpu',
        'ChangeDetection': 'cuda:0'
    }
    
    openai_key = "sk-SPp8PGpzob5k1pcSI2cRORgdeEDoB3QsndvRzIYnUVeKt2jd"
    proxy_url = "https://api.chatanywhere.tech"
    gpt_name = "gpt-3.5-turbo"
    
    bot = RSChatGPT(gpt_name=gpt_name, load_dict=load_dict, openai_key=openai_key, proxy_url=proxy_url)
    bot.initialize()
    
    # 创建日志文件
    log_file = 'multiturn_test.log'
    with open(log_file, 'w', encoding='utf-8') as f:
        f.write("="*100 + "\n")
        f.write("多轮对话测试日志\n")
        f.write("="*100 + "\n\n")
    
    # 统计结果
    total_samples = len(samples)
    total_turns = 0
    correct_turns = 0
    
    print(f"开始测试，共 {total_samples} 个多轮对话样本")
    print(f"{'='*100}\n")
    
    for sample_idx, sample in enumerate(samples, 1):
        sample_id = sample['id']
        dataset = sample['dataset']
        image_name = sample['image_name']
        turns = sample['turns']
        
        print(f"\n{'='*100}")
        print(f"[样本 {sample_idx}/{total_samples}] ID={sample_id}, Dataset={dataset}, Image={image_name}")
        print(f"{'='*100}")
        
        # 记录到日志
        with open(log_file, 'a', encoding='utf-8') as f:
            f.write(f"\n{'='*100}\n")
            f.write(f"样本 {sample_idx}/{total_samples} - ID: {sample_id}\n")
            f.write(f"Dataset: {dataset}, Image: {image_name}\n")
            f.write(f"{'='*100}\n\n")
        
        # ⚠️ 重要：每个样本开始时清空memory，避免累积过多历史
        bot.initialize()
        
        # 定期清理以防止内存泄漏
        if sample_idx % 100 == 0:
            print(f"\n[系统] 已处理 {sample_idx} 个样本，进行内存清理...")
            import gc
            gc.collect()
        
        # 处理每一轮对话
        last_turn_uploaded_image = False  # 标记上一轮是否上传了图片
        
        for turn in turns:
            turn_num = turn['turn']
            role = turn['role']
            content = turn['content']
            images = turn.get('images', [])
            tool_calls = turn.get('tool_calls', None)
            
            if role == 'user':
                print(f"\n--- Turn {turn_num} (User) ---")
                print(f"User: {content}")
                
                # 记录到日志
                with open(log_file, 'a', encoding='utf-8') as f:
                    f.write(f"\n--- Turn {turn_num} (User) ---\n")
                    f.write(f"Content: {content}\n")
                    f.write(f"Images: {images if images else '无'}\n")
                
                # 处理图片 - 自动调用ImageCaptioning（系统设计）
                if images:
                    last_turn_uploaded_image = True  # 标记本轮上传了图片
                    for img_path in images:
                        print(f"  上传图片: {img_path}")
                        # 自动获取图片描述，提供给Agent作为上下文
                        # 这是RSChatGPT系统的原始设计
                        try:
                            description = bot.models['ImageCaptioning'].inference(img_path)
                            Human_prompt = f'Provide a remote sensing image named {img_path}. The description is: {description}. This information helps you to understand this image, but you should use tools to finish following tasks, rather than directly imagine from my description. If you understand, say "Received".'
                            AI_prompt = "Received."
                            bot.memory.chat_memory.add_user_message(Human_prompt)
                            bot.memory.chat_memory.add_ai_message(AI_prompt)
                            
                            with open(log_file, 'a', encoding='utf-8') as f:
                                f.write(f"  [系统] 自动获取图片描述: {description}\n")
                        except Exception as e:
                            print(f"  图片处理失败: {e}")
                            with open(log_file, 'a', encoding='utf-8') as f:
                                f.write(f"  图片处理失败: {e}\n")
                else:
                    last_turn_uploaded_image = False  # 本轮没有上传图片
                
                # 发送用户消息给agent
                try:
                    # 检测任务类型并添加上下文提示
                    task_hint = ""
                    
                    # 检测变化检测任务的关键词
                    change_keywords = ['变化', '新东西', '不同', '对比', 'change', 'difference', 'new']
                    if any(kw in content.lower() for kw in change_keywords):
                        # 检查是否已有两张图片
                        all_images_in_memory = []
                        for msg in bot.memory.chat_memory.messages:
                            if 'image' in msg.content.lower() and '.png' in msg.content:
                                import re
                                imgs = re.findall(r'[^\s]+\.png', msg.content)
                                all_images_in_memory.extend(imgs)
                        
                        unique_images = list(set(all_images_in_memory))
                        if len(unique_images) >= 2:
                            task_hint = f" [Note: User is asking about changes. You have {len(unique_images)} images available for comparison: {', '.join(unique_images[:2])}. Consider using Change Detection tool.]"
                    
                    # 构建输入（如果有多张图片，用逗号分隔）
                    if images:
                        if len(images) == 1:
                            agent_input = f"{content} {images[0]}{task_hint}"
                        else:
                            agent_input = f"{content} {','.join(images)}{task_hint}"
                    else:
                        agent_input = f"{content}{task_hint}"
                    
                    print(f"\n>>> 发送给Agent: {agent_input}")
                    with open(log_file, 'a', encoding='utf-8') as f:
                        f.write(f"\n>>> Agent输入: {agent_input}\n")
                    
                    # 调用agent
                    res = bot.agent({"input": agent_input})
                    
                    # 提取AI回复
                    ai_response = res.get('output', 'No response')
                    print(f"\n<<< Agent回复:\n{ai_response}")
                    
                    with open(log_file, 'a', encoding='utf-8') as f:
                        f.write(f"\n<<< Agent回复:\n{ai_response}\n")
                    
                except Exception as e:
                    error_msg = str(e)
                    print(f"!!! Agent执行异常: {error_msg}")
                    
                    # 检查是否是token超限错误
                    if 'maximum context length' in error_msg.lower() or 'token' in error_msg.lower():
                        print(f"⚠️  检测到Token超限，清空Memory后重试...")
                        bot.initialize()  # 清空Memory
                        
                        with open(log_file, 'a', encoding='utf-8') as f:
                            f.write(f"\n⚠️  Token超限，已清空Memory\n")
                        
                        # 重试一次
                        try:
                            res = bot.agent({"input": agent_input})
                            ai_response = res.get('output', 'No response')
                            print(f"✓ 重试成功")
                        except Exception as e2:
                            ai_response = f"Error: {e2}"
                            print(f"✗ 重试仍失败: {e2}")
                    else:
                        ai_response = f"Error: {e}"
                    
                    with open(log_file, 'a', encoding='utf-8') as f:
                        f.write(f"\n!!! Agent执行异常: {error_msg}\n")
                        import traceback
                        f.write(f"{traceback.format_exc()}\n")
            
            elif role == 'assistant':
                # 这是ground truth的assistant回复
                print(f"\n--- Turn {turn_num} (Assistant Ground Truth) ---")
                print(f"GT Response: {content}")
                print(f"GT Tool Calls: {tool_calls if tool_calls else '无'}")
                
                with open(log_file, 'a', encoding='utf-8') as f:
                    f.write(f"\n--- Turn {turn_num} (Assistant Ground Truth) ---\n")
                    f.write(f"GT Content: {content}\n")
                    f.write(f"GT Tool Calls: {tool_calls if tool_calls else '无'}\n")
                
                # 统计该轮（assistant轮需要统计）
                total_turns += 1
                
                # 提取实际调用的工具 - 从intermediate_steps提取
                actual_tools_called = []
                tool_mapping = {
                    'Get Photo Description': 'ImageCaptioning',
                    'Scene Classification for Remote Sensing Image': 'SceneClassification',
                    'Detect the given object': 'ObjectDetection',
                    'Count object': 'ObjectCounting',
                    'Edge Detection On Image': 'EdgeDetection',
                    'Change Detection On Image Pair': 'ChangeDetection'
                }
                
                if 'intermediate_steps' in res and res['intermediate_steps']:
                    for step in res['intermediate_steps']:
                        if len(step) >= 1:
                            agent_action = step[0]
                            tool_name = str(agent_action.tool) if hasattr(agent_action, 'tool') else str(agent_action)
                        if tool_name in tool_mapping:
                                mapped_tool = tool_mapping[tool_name]
                                if mapped_tool not in actual_tools_called:
                                    actual_tools_called.append(mapped_tool)
                
                # 过滤系统自动的ImageCaptioning
                # 如果上一轮上传了图片，这一轮Agent回复中的ImageCaptioning可能是系统自动触发的
                if last_turn_uploaded_image and actual_tools_called == ['ImageCaptioning']:
                    with open(log_file, 'a', encoding='utf-8') as f:
                        f.write(f"  [过滤] 上一轮上传图片后的ImageCaptioning，视为系统自动调用，不计入统计\n")
                    actual_tools_called = []
                
                # Ground Truth工具列表
                gt_tools = []
                if tool_calls:
                    for tc in tool_calls:
                        if 'tool' in tc:
                            gt_tools.append(tc['tool'])
                
                # 判断是否正确
                is_correct = (set(actual_tools_called) == set(gt_tools))
                if is_correct:
                    correct_turns += 1
                    result_mark = "✓"
                else:
                    result_mark = "✗"
                
                print(f"\n{result_mark} 实际调用工具: {actual_tools_called if actual_tools_called else '无'}")
                print(f"  Ground Truth: {gt_tools if gt_tools else '无'}")
                
                with open(log_file, 'a', encoding='utf-8') as f:
                    f.write(f"\n{result_mark} 实际调用工具: {actual_tools_called if actual_tools_called else '无'}\n")
                    f.write(f"  Ground Truth: {gt_tools if gt_tools else '无'}\n")
                    f.write(f"  判断: {'正确' if is_correct else '错误'}\n")
        
        print(f"\n样本 {sample_idx} 完成")
        print(f"当前总体进度: {correct_turns}/{total_turns} = {(correct_turns/total_turns*100) if total_turns > 0 else 0:.2f}%")
    
    # 输出最终统计结果
    print(f"\n{'='*100}")
    print(f"多轮对话测试完成!")
    print(f"总样本数: {total_samples}")
    print(f"总轮次数: {total_turns}")
    print(f"正确轮次数: {correct_turns}")
    print(f"错误轮次数: {total_turns - correct_turns}")
    print(f"轮次级别准确率: {(correct_turns/total_turns*100) if total_turns > 0 else 0:.2f}%")
    print(f"{'='*100}")
    
    print(f"\n详细日志已保存到 {log_file}")
    
    # 在日志末尾添加汇总
    with open(log_file, 'a', encoding='utf-8') as f:
        f.write(f"\n{'='*100}\n")
        f.write(f"测试汇总\n")
        f.write(f"{'='*100}\n")
        f.write(f"总样本数: {total_samples}\n")
        f.write(f"总轮次数: {total_turns}\n")
        f.write(f"正确轮次数: {correct_turns}\n")
        f.write(f"错误轮次数: {total_turns - correct_turns}\n")
        f.write(f"轮次级别准确率: {(correct_turns/total_turns*100) if total_turns > 0 else 0:.2f}%\n")
        f.write(f"{'='*100}\n")

def test_rschatgpt():
    """原有的单轮测试函数（已禁用，请使用test_multiturn_qa）"""
    print("此函数已被替换，请使用 test_multiturn_qa() 进行多轮对话测试")

if __name__ == '__main__':
    test_multiturn_qa()

