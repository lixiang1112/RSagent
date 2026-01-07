import json
import os
import sys
import importlib.util
import csv
import re
import io
from contextlib import redirect_stdout, redirect_stderr
import numpy as np
from skimage import io as skio
import cv2
from PIL import Image, ImageDraw, ImageFont

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

def test_rschatgpt():
    # 加载问题
    with open('RSquestion.json', 'r', encoding='utf-8') as f:
        questions = json.load(f)
    
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
    
    # 创建CSV文件并写入表头
    csv_file = 'test_results.csv'
    with open(csv_file, 'w', newline='', encoding='utf-8-sig') as f:
        writer = csv.writer(f)
        writer.writerow(['问题序号', '问题内容', 'Ground Truth Tool', '实际调用Tool', '是否正确'])
    
    # 创建详细日志文件
    detail_log_file = 'test_details.txt'
    with open(detail_log_file, 'w', encoding='utf-8') as f:
        f.write("="*100 + "\n")
        f.write("RSChatGPT 测试详细日志\n")
        f.write("="*100 + "\n\n")
    
    # 统计结果
    # 可以修改这里来测试指定数量的问题
    # questions = questions[:5]  # 只测试前5个
    # questions = [q for q in questions if q['id'] >= 121]  # 测试新增的6个问题
    total = len(questions)
    correct = 0
    
    # 按工具类别统计
    from collections import defaultdict
    tool_stats = defaultdict(lambda: {'total': 0, 'correct': 0})
    
    print(f"开始测试，共 {total} 个问题")
    print(f"{'='*100}")
    
    for i, item in enumerate(questions):
        question_num = i + 1
        question_text = item['query']
        ground_truth_tool = item['tool']
        
        print(f"\n[{question_num}/{total}] 测试问题 ID={item['id']}")
        print(f"问题: {question_text}")
        print(f"Ground Truth: {ground_truth_tool}")
        
        # 记录到详细日志
        with open(detail_log_file, 'a', encoding='utf-8') as f:
            f.write(f"\n{'='*100}\n")
            f.write(f"问题 {question_num}/{total} - ID: {item['id']}\n")
            f.write(f"{'='*100}\n")
            f.write(f"问题内容: {question_text}\n")
            f.write(f"Ground Truth Tool: {ground_truth_tool}\n")
            f.write(f"图片路径: {item['image']}\n")
            f.write(f"\n--- Agent执行过程 ---\n")
            f.write(f"注意：Agent的详细执行过程会显示在终端输出中\n")
            f.write(f"这里仅记录工具调用的关键信息\n\n")
        
        try:
            state = []
            
            # 处理图片输入
            from skimage import io as skio
            import numpy as np
            
            if isinstance(item['image'], list):
                # ChangeDetection需要两张图（前后对比）
                image_path_before = item['image'][0]
                image_path_after = item['image'][1]
                query = item['query']
                
                # 直接使用原始图片路径
                image_filename_before = image_path_before
                image_filename_after = image_path_after
                image_filename = image_filename_before
                
                # 获取图片描述
                description = bot.models['ImageCaptioning'].inference(image_filename)
            else:
                # 其他工具只需要一张图
                image_path = item['image']
                query = item['query']
                
                # 直接使用原始图片路径
                image_filename = image_path
                
                # 获取图片描述
                description = bot.models['ImageCaptioning'].inference(image_filename)
            
            Human_prompt = f' Provide a remote sensing image named {image_filename}. The description is: {description}. This information helps you to understand this image, but you should use tools to finish following tasks, rather than directly imagine from my description. If you understand, say "Received".'
            AI_prompt = "Received."
            bot.memory.chat_memory.add_user_message(Human_prompt)
            bot.memory.chat_memory.add_ai_message(AI_prompt)
            
            state = state + [(f"![](file={image_filename})*{image_filename}*", AI_prompt)]
            
            # 运行agent并获取intermediate_steps
            # 注意：不使用redirect_stdout，让输出正常显示，同时通过tee方式记录
            agent_error = None
            try:
                # 对于变化检测，需要传递两张图片的路径
                if isinstance(item['image'], list):
                    # 变化检测：传递两张图片路径
                    agent_input = f'{query} {image_filename_before},{image_filename_after} '.strip()
                else:
                    # 其他工具：传递单张图片路径
                    agent_input = f'{query} {image_filename} '.strip()
                
                # 直接运行agent，输出会正常打印到终端
                res = bot.agent({"input": agent_input})
            except Exception as e:
                # 如果agent执行失败
                print(f"Agent执行异常: {e}")
                agent_error = str(e)
                res = {'intermediate_steps': [], 'output': str(e)}
                
                # 记录错误到详细日志
                with open(detail_log_file, 'a', encoding='utf-8') as f:
                    f.write(f"\n!!! Agent执行异常: {agent_error}\n")
            
            # 从intermediate_steps中提取工具调用（第一个工具调用是主要任务）
            actual_tool = "Unknown"
            
            if 'intermediate_steps' in res and res['intermediate_steps']:
                # intermediate_steps是一个列表，每个元素是 (AgentAction, observation)
                # 取第一个工具调用作为主要任务
                for step in res['intermediate_steps']:
                    if len(step) >= 1:
                        agent_action = step[0]
                        tool_name = str(agent_action.tool) if hasattr(agent_action, 'tool') else str(agent_action)
                        
                        # 映射工具名称
                        tool_mapping = {
                            'Get Photo Description': 'ImageCaptioning',
                            'Scene Classification for Remote Sensing Image': 'SceneClassification',
                            'Detect the given object': 'ObjectDetection',
                            'Count object': 'ObjectCounting',
                            'Edge Detection On Image': 'EdgeDetection',
                            'Change Detection On Image Pair': 'ChangeDetection'
                        }
                        
                        if tool_name in tool_mapping:
                            actual_tool = tool_mapping[tool_name]
                            break
            
            # 更新state
            if 'output' in res:
                res['output'] = res['output'].replace("\\", "/")
                response = re.sub('(result/[-\w]*.png)', lambda m: f'![](file={m.group(0)})*{m.group(0)}*', res['output'])
            else:
                response = "Error: No output"
            state = state + [(f'{query} {image_filename} ', response)]
            
            # 判断是否正确
            is_correct = (actual_tool == ground_truth_tool)
            
            # 更新统计
            tool_stats[ground_truth_tool]['total'] += 1
            if is_correct:
                correct += 1
                tool_stats[ground_truth_tool]['correct'] += 1
                result_text = "✓ 正确"
                result_symbol = "✓"
            else:
                result_text = "✗ 错误"
                result_symbol = "✗"
            
            print(f"实际调用: {actual_tool}")
            print(f"结果: {result_text}")
            
            # 后处理结果文件
            if is_correct and 'output' in res:
                output_text = res['output']
                import glob
                import shutil
                
                # 变化检测：拼接before/after/mask
                if ground_truth_tool == 'ChangeDetection':
                    # 查找生成的mask文件（可能在原图目录）
                    mask_files = []
                    for root, dirs, files in os.walk('/root/autodl-tmp/datasets'):
                        for file in files:
                            if 'change_detection' in file and file.endswith('.png'):
                                filepath = os.path.join(root, file)
                                # 检查是否是刚生成的（5秒内）
                                if os.path.getmtime(filepath) > os.path.getmtime(__file__) - 60:
                                    mask_files.append(filepath)
                    
                    if mask_files:
                        latest_mask = max(mask_files, key=os.path.getmtime)
                        combined_output = os.path.join('result', f"q{item['id']:03d}_ChangeDetection_result.png")
                        post_process_change_detection(
                            image_path_before, 
                            image_path_after, 
                            latest_mask, 
                            combined_output,
                            item['id']
                        )
                
                # 边缘检测：移动结果图到result目录
                elif ground_truth_tool == 'EdgeDetection':
                    edge_files = []
                    for root, dirs, files in os.walk('/root/autodl-tmp/datasets'):
                        for file in files:
                            if 'edge' in file and file.endswith('.png'):
                                filepath = os.path.join(root, file)
                                if os.path.getmtime(filepath) > os.path.getmtime(__file__) - 60:
                                    edge_files.append(filepath)
                    
                    if edge_files:
                        latest_edge = max(edge_files, key=os.path.getmtime)
                        edge_output = os.path.join('result', f"q{item['id']:03d}_EdgeDetection_result.png")
                        shutil.copy2(latest_edge, edge_output)
                        print(f"✓ 边缘检测结果已保存: {edge_output}")
                
                # 目标检测/计数：查找txt文件
                elif ground_truth_tool in ['ObjectDetection', 'ObjectCounting']:
                    txt_files = []
                    for root, dirs, files in os.walk('/root/autodl-tmp/datasets'):
                        for file in files:
                            if 'detection' in file and file.endswith('.txt'):
                                filepath = os.path.join(root, file)
                                if os.path.getmtime(filepath) > os.path.getmtime(__file__) - 60:
                                    txt_files.append(filepath)
                    
                    if txt_files:
                        latest_txt = max(txt_files, key=os.path.getmtime)
                        print(f"  检测结果坐标文件: {latest_txt}")
                        # TODO: 绘制边界框
            
            # 保存文本结果到文件（针对文本输出工具）
            text_output_tools = ['ImageCaptioning', 'SceneClassification', 'ObjectCounting']
            if ground_truth_tool in text_output_tools and 'output' in res:
                # 提取纯文本结果
                clean_text = extract_text_from_output(res['output'], ground_truth_tool)
                
                result_text_file = os.path.join('result', f"q{item['id']:03d}_{ground_truth_tool}_result.txt")
                with open(result_text_file, 'w', encoding='utf-8') as tf:
                    tf.write(clean_text)
                print(f"✓ 文本结果已保存: {result_text_file}")
            
            # 记录结果到详细日志
            with open(detail_log_file, 'a', encoding='utf-8') as f:
                f.write(f"\n--- 提取结果 ---\n")
                f.write(f"实际调用Tool: {actual_tool}\n")
                f.write(f"Ground Truth Tool: {ground_truth_tool}\n")
                f.write(f"判断结果: {result_text}\n")
                if not is_correct:
                    f.write(f"\n!!! 错误原因分析 !!!\n")
                    f.write(f"期望工具: {ground_truth_tool}\n")
                    f.write(f"实际工具: {actual_tool}\n")
                    if 'intermediate_steps' in res:
                        f.write(f"Intermediate steps数量: {len(res['intermediate_steps'])}\n")
                        if res['intermediate_steps']:
                            for idx, step in enumerate(res['intermediate_steps']):
                                if len(step) >= 1:
                                    f.write(f"  Step {idx}: {step[0]}\n")
                f.write(f"\n")
                
        except Exception as e:
            actual_tool = "Error"
            result_symbol = "✗"
            error_msg = str(e)
            print(f"✗ 发生错误: {error_msg}")
            
            # 记录错误到详细日志
            with open(detail_log_file, 'a', encoding='utf-8') as f:
                f.write(f"\n!!! 程序异常 !!!\n")
                f.write(f"错误信息: {error_msg}\n")
                import traceback
                f.write(f"堆栈跟踪:\n{traceback.format_exc()}\n")
        
        # 立即写入CSV文件
        with open(csv_file, 'a', newline='', encoding='utf-8-sig') as f:
            writer = csv.writer(f)
            writer.writerow([
                question_num,
                question_text,
                ground_truth_tool,
                actual_tool,
                result_symbol
            ])
        
        # 显示当前进度
        current_accuracy = (correct / question_num) * 100
        print(f"当前进度: {question_num}/{total}, 正确率: {current_accuracy:.2f}%")
        
        # 清空memory
        bot.initialize()
    
    # 输出最终统计结果
    print(f"\n{'='*100}")
    print(f"测试完成!")
    print(f"总问题数: {total}")
    print(f"正确数量: {correct}")
    print(f"错误数量: {total - correct}")
    print(f"总正确率: {(correct/total*100):.2f}%")
    
    # 输出每个工具类别的统计
    print(f"\n{'='*100}")
    print(f"每个工具类别的正确率:")
    print(f"{'='*100}")
    print(f"{'工具名称':<30} {'总数':>8} {'正确':>8} {'错误':>8} {'正确率':>10}")
    print(f"{'-'*100}")
    
    for tool in sorted(tool_stats.keys()):
        stats = tool_stats[tool]
        tool_total = stats['total']
        tool_correct = stats['correct']
        tool_incorrect = tool_total - tool_correct
        tool_accuracy = (tool_correct / tool_total * 100) if tool_total > 0 else 0
        print(f"{tool:<30} {tool_total:>8} {tool_correct:>8} {tool_incorrect:>8} {tool_accuracy:>9.2f}%")
    
    print(f"{'-'*100}")
    print(f"{'总计':<30} {total:>8} {correct:>8} {total-correct:>8} {(correct/total*100):>9.2f}%")
    print(f"{'='*100}")
    
    print(f"\n详细结果已保存到 {csv_file}")
    print(f"详细日志已保存到 {detail_log_file}")
    
    # 同时保存JSON格式的汇总（包含每个工具的统计）
    summary_data = {
        'overall': {
            'total': total,
            'correct': correct,
            'incorrect': total - correct,
            'accuracy': f"{(correct/total*100):.2f}%"
        },
        'by_tool': {}
    }
    
    for tool in sorted(tool_stats.keys()):
        stats = tool_stats[tool]
        tool_total = stats['total']
        tool_correct = stats['correct']
        summary_data['by_tool'][tool] = {
            'total': tool_total,
            'correct': tool_correct,
            'incorrect': tool_total - tool_correct,
            'accuracy': f"{(tool_correct/tool_total*100):.2f}%" if tool_total > 0 else "0.00%"
        }
    
    with open('test_summary.json', 'w', encoding='utf-8') as f:
        json.dump(summary_data, f, ensure_ascii=False, indent=2)
    
    # 在详细日志末尾添加汇总
    with open(detail_log_file, 'a', encoding='utf-8') as f:
        f.write(f"\n{'='*100}\n")
        f.write(f"测试汇总\n")
        f.write(f"{'='*100}\n")
        f.write(f"总问题数: {total}\n")
        f.write(f"正确数量: {correct}\n")
        f.write(f"错误数量: {total - correct}\n")
        f.write(f"总正确率: {(correct/total*100):.2f}%\n\n")
        
        f.write(f"{'='*100}\n")
        f.write(f"每个工具类别的正确率:\n")
        f.write(f"{'='*100}\n")
        f.write(f"{'工具名称':<30} {'总数':>8} {'正确':>8} {'错误':>8} {'正确率':>10}\n")
        f.write(f"{'-'*100}\n")
        
        for tool in sorted(tool_stats.keys()):
            stats = tool_stats[tool]
            tool_total = stats['total']
            tool_correct = stats['correct']
            tool_incorrect = tool_total - tool_correct
            tool_accuracy = (tool_correct / tool_total * 100) if tool_total > 0 else 0
            f.write(f"{tool:<30} {tool_total:>8} {tool_correct:>8} {tool_incorrect:>8} {tool_accuracy:>9.2f}%\n")
        
        f.write(f"{'-'*100}\n")
        f.write(f"{'总计':<30} {total:>8} {correct:>8} {total-correct:>8} {(correct/total*100):>9.2f}%\n")
        f.write(f"{'='*100}\n")

if __name__ == '__main__':
    test_rschatgpt()

