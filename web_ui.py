#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
遥感 Agent Web UI - 高颜值暗色主题界面
支持图文上传、多轮对话、工具自选
"""

import os
import sys
import argparse
import traceback
import uuid
from datetime import datetime
from typing import List, Tuple, Optional
import gradio as gr
from skimage import io
import numpy as np

# 动态导入 RSChatGPT-shell.py（因为文件名包含连字符）
import importlib.util
spec = importlib.util.spec_from_file_location(
    "rschatgpt_shell", 
    os.path.join(os.path.dirname(__file__), "RSChatGPT-shell.py")
)
rschatgpt_shell = importlib.util.module_from_spec(spec)
sys.modules["rschatgpt_shell"] = rschatgpt_shell
spec.loader.exec_module(rschatgpt_shell)
RSChatGPT = rschatgpt_shell.RSChatGPT


# ==================== 自定义 CSS 样式 ====================
CUSTOM_CSS = """
/* 全局样式 */
.gradio-container {
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif !important;
    background: radial-gradient(circle at 50% 0%, #262730, #0e1117) !important;
    color: #ffffff !important;
}

/* 主容器 */
#main-container {
    max-width: 1400px;
    margin: 0 auto;
    padding: 20px;
}

/* 标题区 */
#title-container {
    text-align: center;
    margin-bottom: 30px;
}

#main-title {
    font-size: 36px;
    font-weight: 600;
    color: #ffffff;
    margin-bottom: 8px;
    letter-spacing: -0.5px;
}

#title-highlight {
    width: 60px;
    height: 4px;
    background: #00c896;
    margin: 0 auto 12px;
    border-radius: 2px;
}

#subtitle {
    font-size: 13px;
    color: rgba(255, 255, 255, 0.6);
    font-weight: 400;
}

/* 卡片样式 */
.card {
    background: rgba(255, 255, 255, 0.03) !important;
    border: 1px solid rgba(255, 255, 255, 0.08) !important;
    border-radius: 8px !important;
    box-shadow: 0 4px 20px rgba(0, 0, 0, 0.25) !important;
    padding: 20px !important;
}

/* 上传区域 */
.upload-area {
    min-height: 140px !important;
    background: rgba(255, 255, 255, 0.05) !important;
    border: 2px dashed rgba(255, 255, 255, 0.2) !important;
    border-radius: 8px !important;
    transition: all 0.2s ease !important;
}

.upload-area:hover {
    border-color: #00c896 !important;
    background: rgba(0, 200, 150, 0.05) !important;
}

/* 双图上传布局 */
.upload-area img {
    max-height: 120px !important;
    object-fit: contain !important;
}

/* 工具选择区 */
.tool-checkbox label {
    font-size: 13px !important;
    line-height: 1.5 !important;
    color: rgba(255, 255, 255, 0.9) !important;
    white-space: nowrap !important;
    overflow: hidden !important;
    text-overflow: ellipsis !important;
}

.tool-checkbox {
    display: flex !important;
    flex-direction: column !important;
    gap: 8px !important;
    max-height: 450px !important;
    overflow-y: auto !important;
}

.tool-checkbox > label {
    padding: 8px 12px !important;
    background: rgba(255, 255, 255, 0.03) !important;
    border-radius: 6px !important;
    transition: all 0.2s ease !important;
}

.tool-checkbox > label:hover {
    background: rgba(0, 200, 150, 0.08) !important;
}

/* 主按钮 */
.primary-btn {
    background: linear-gradient(90deg, #00c896, #005fee) !important;
    border: none !important;
    color: white !important;
    font-size: 14px !important;
    font-weight: 500 !important;
    padding: 12px 24px !important;
    border-radius: 8px !important;
    transition: all 0.2s ease !important;
    cursor: pointer !important;
}

.primary-btn:hover {
    filter: brightness(1.1) !important;
    transform: translateY(-1px) !important;
}

/* 幽灵按钮 */
.ghost-btn {
    background: transparent !important;
    border: 1px solid rgba(255, 255, 255, 0.3) !important;
    color: rgba(255, 255, 255, 0.9) !important;
    font-size: 14px !important;
    padding: 10px 20px !important;
    border-radius: 8px !important;
    transition: all 0.2s ease !important;
}

.ghost-btn:hover {
    border-color: #00c896 !important;
    background: rgba(0, 200, 150, 0.1) !important;
}

/* 聊天窗口 */
.chatbot-container {
    height: 520px !important;
    background: rgba(255, 255, 255, 0.03) !important;
    border: 1px solid rgba(255, 255, 255, 0.08) !important;
    border-radius: 8px !important;
    overflow-y: auto !important;
}

/* 用户消息气泡 */
.message.user {
    background: #005fee !important;
    color: white !important;
    border-radius: 12px !important;
    padding: 12px 16px !important;
    font-size: 15px !important;
    line-height: 1.6 !important;
}

/* 助手消息气泡 */
.message.bot {
    background: rgba(255, 255, 255, 0.06) !important;
    color: rgba(255, 255, 255, 0.95) !important;
    border-radius: 12px !important;
    padding: 12px 16px !important;
    font-size: 15px !important;
    line-height: 1.6 !important;
}

/* 输入框 */
.input-box textarea {
    background: rgba(255, 255, 255, 0.05) !important;
    border: 1px solid rgba(255, 255, 255, 0.1) !important;
    border-radius: 20px !important;
    color: white !important;
    font-size: 15px !important;
    padding: 12px 20px !important;
    transition: all 0.2s ease !important;
}

.input-box textarea:focus {
    border-color: #00c896 !important;
    background: rgba(255, 255, 255, 0.08) !important;
    outline: none !important;
}

/* 发送按钮 */
.send-btn {
    background: linear-gradient(90deg, #00c896, #005fee) !important;
    border: none !important;
    color: white !important;
    font-size: 18px !important;
    width: 50px !important;
    height: 50px !important;
    border-radius: 25px !important;
    transition: all 0.2s ease !important;
    display: flex !important;
    align-items: center !important;
    justify-content: center !important;
}

.send-btn:hover {
    filter: brightness(1.2) !important;
    transform: scale(1.05) !important;
}

/* 滚动条样式 */
::-webkit-scrollbar {
    width: 6px !important;
    height: 6px !important;
}

::-webkit-scrollbar-track {
    background: rgba(255, 255, 255, 0.05) !important;
    border-radius: 3px !important;
}

::-webkit-scrollbar-thumb {
    background: #00c896 !important;
    border-radius: 3px !important;
}

::-webkit-scrollbar-thumb:hover {
    background: #00e0a8 !important;
}

/* 状态文本 */
.status-text {
    font-size: 13px !important;
    color: rgba(255, 255, 255, 0.7) !important;
    padding: 8px 12px !important;
    border-radius: 6px !important;
    background: rgba(255, 255, 255, 0.05) !important;
}

.status-success {
    color: #00c896 !important;
    background: rgba(0, 200, 150, 0.1) !important;
}

.status-error {
    color: #ff4d4f !important;
    background: rgba(255, 77, 79, 0.1) !important;
}

/* Gradio 组件覆盖 */
.gr-button {
    transition: all 0.2s ease !important;
}

.gr-form {
    background: transparent !important;
    border: none !important;
}

.gr-box {
    background: rgba(255, 255, 255, 0.03) !important;
    border: 1px solid rgba(255, 255, 255, 0.08) !important;
    border-radius: 8px !important;
}

.gr-input {
    background: rgba(255, 255, 255, 0.05) !important;
    border: 1px solid rgba(255, 255, 255, 0.1) !important;
    color: white !important;
}

.gr-text-input:focus {
    border-color: #00c896 !important;
}

/* 工具图标映射 */
.tool-icon::before {
    margin-right: 8px;
}
"""


# ==================== 全局配置 ====================
IMAGE_SAVE_DIR = os.path.join(os.path.dirname(__file__), "image")
os.makedirs(IMAGE_SAVE_DIR, exist_ok=True)

DEFAULT_LOAD_DICT = {
    "ImageCaptioning": "cuda:0",
    "SceneClassification": "cuda:0",
    "ObjectDetection": "cuda:0",
    "ObjectCounting": "cuda:0",
    "EdgeDetection": "cpu",
    "ChangeDetection": "cuda:0"
}

# 工具图标映射
TOOL_ICONS = {
    "Get Photo Description": "🖼️",
    "Edge Detection On Image": "🔍",
    "Change Detection On Image Pair": "🔄",
    "Count object": "📏",
    "Instance Segmentation for Remote Sensing Image": "🏞️",
    "Scene Classification for Remote Sensing Image": "🛰️",
    "Land Use Segmentation for Remote Sensing Image": "🌍",
    "Detect the given object": "🎯",
    "Cloud Removal On Image": "☁️",
    "Super Resolution On Image": "✨",
    "Denoising On Image": "🔧",
    "Horizontal Detection On Image": "📐",
    "Rotated Detection On Image": "🔄"
}


# ==================== 辅助函数 ====================

def save_uploaded_image(uploaded_file) -> Optional[str]:
    """保存用户上传的图片到 image 目录"""
    if uploaded_file is None:
        return None
    
    try:
        # 处理 Gradio 传递的文件对象或字符串路径
        if isinstance(uploaded_file, str):
            # 如果是字符串路径，直接读取
            source_path = uploaded_file
        else:
            # 如果是文件对象，获取其路径
            source_path = uploaded_file.name
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        random_id = str(uuid.uuid4())[:8]
        ext = os.path.splitext(source_path)[-1] or ".png"
        filename = f"{timestamp}_{random_id}{ext}"
        save_path = os.path.join(IMAGE_SAVE_DIR, filename)
        
        img = io.imread(source_path)
        io.imsave(save_path, img.astype(np.uint8))
        
        print(f"✓ 图片已保存: {save_path}")
        return save_path
    except Exception as e:
        print(f"✗ 保存图片失败: {e}")
        traceback.print_exc()
        return None


def format_error(error: Exception) -> str:
    """将异常信息格式化为 Markdown 折叠代码块"""
    error_trace = traceback.format_exc()
    return f"""
<details style="color: #ff4d4f;">
<summary>⚠️ 发生错误，点击展开详情</summary>

```python
{error_trace}
```
</details>
"""


def initialize_agent(
    gpt_name: str,
    openai_key: str,
    proxy_url: str,
    load_dict: dict,
    enable_query_optimization: bool = False
) -> RSChatGPT:
    """初始化 RSChatGPT Agent"""
    try:
        bot = RSChatGPT(
            gpt_name=gpt_name,
            load_dict=load_dict,
            openai_key=openai_key,
            proxy_url=proxy_url,
            enable_query_optimization=enable_query_optimization
        )
        bot.initialize()
        print("✓ Agent 初始化成功")
        return bot
    except Exception as e:
        print(f"✗ Agent 初始化失败: {e}")
        traceback.print_exc()
        raise


def get_tool_list(agent: RSChatGPT) -> List[str]:
    """从 Agent 中提取所有可用工具的名称（带图标）"""
    if agent is None:
        return []
    tools = []
    for tool in agent.tools:
        icon = TOOL_ICONS.get(tool.name, "🔧")
        tools.append(f"{icon} {tool.name}")
    return tools


def filter_tools(agent: RSChatGPT, selected_tools: List[str]) -> RSChatGPT:
    """根据用户选择的工具过滤 Agent 的工具列表"""
    if agent is None:
        return agent
    
    # 移除图标前缀
    clean_selected = [t.split(" ", 1)[1] if " " in t else t for t in selected_tools]
    
    # 过滤工具
    agent.tools = [tool for tool in agent.tools if tool.name in clean_selected]
    agent.initialize()
    
    print(f"✓ 已更新工具列表，当前启用 {len(agent.tools)} 个工具")
    return agent


# ==================== Gradio 回调函数 ====================

def handle_image_upload(
    uploaded_file,
    agent: RSChatGPT,
    chat_history: List[Tuple[str, str]],
    current_image_path: str
) -> Tuple[str, List[Tuple[str, str]], str]:
    """处理用户上传的图片"""
    try:
        image_path = save_uploaded_image(uploaded_file)
        if image_path is None:
            return current_image_path, chat_history, "❌ 图片上传失败"
        
        if agent is not None:
            try:
                state = agent.run_image(image_path, chat_history, txt=None)
                filename = os.path.basename(image_path)
                return image_path, state, f"✅ 已上传 {filename}"
            except Exception as e:
                error_msg = format_error(e)
                chat_history.append((f"🧑‍🚀 上传图片: {os.path.basename(image_path)}", f"🤖 {error_msg}"))
                return image_path, chat_history, "⚠️ 图片已保存，但处理时出错"
        else:
            return image_path, chat_history, "⚠️ Agent 未初始化"
            
    except Exception as e:
        return current_image_path, chat_history, f"❌ 上传失败: {str(e)}"


def handle_text_input(
    user_input: str,
    agent: RSChatGPT,
    chat_history: List[Tuple[str, str]],
    current_image_path: str,
    second_image_path: str,
    selected_tools: List[str]
) -> Tuple[List[Tuple[str, str]], str]:
    """处理用户的文本输入"""
    if not user_input.strip():
        return chat_history, ""
    
    if agent is None:
        chat_history.append((f"🧑‍🚀 {user_input}", "🤖 ❌ Agent 未初始化，请先重新加载"))
        return chat_history, ""
    
    try:
        agent = filter_tools(agent, selected_tools)
        
        # 智能处理图片路径
        text_with_image = user_input
        
        # 检查是否需要两张图片（变化检测相关任务）
        is_change_detection = any(keyword in user_input.lower() for keyword in 
                                 ['变化', 'change', '对比', 'compare', '差异', 'difference'])
        
        # 验证图片路径是否存在
        img1_valid = current_image_path and os.path.exists(current_image_path)
        img2_valid = second_image_path and os.path.exists(second_image_path)
        
        if is_change_detection and img1_valid and img2_valid:
            # 变化检测任务：需要两张图片
            if current_image_path not in user_input and second_image_path not in user_input:
                text_with_image = f"{user_input} {current_image_path},{second_image_path}"
        elif img1_valid:
            # 单图任务：只需要一张图片
            if current_image_path not in user_input:
                text_with_image = f"{user_input} {current_image_path}"
        elif not img1_valid and not img2_valid:
            # 没有有效图片
            chat_history.append((f"🧑‍🚀 {user_input}", "🤖 ⚠️ 请先上传图片"))
            return chat_history, ""
        
        state = agent.run_text(text_with_image, chat_history)
        
        # 添加 emoji 头像
        formatted_state = []
        for user_msg, bot_msg in state:
            if not user_msg.startswith("🧑‍🚀"):
                user_msg = f"🧑‍🚀 {user_msg}"
            if not bot_msg.startswith("🤖"):
                bot_msg = f"🤖 {bot_msg}"
            formatted_state.append((user_msg, bot_msg))
        
        return formatted_state, ""
        
    except Exception as e:
        print(f"❌ 处理文本输入时出错: {e}")
        traceback.print_exc()
        error_msg = format_error(e)
        chat_history.append((f"🧑‍🚀 {user_input}", f"🤖 {error_msg}"))
        return chat_history, ""


def reload_agent(
    agent: RSChatGPT,
    gpt_name: str,
    openai_key: str,
    proxy_url: str
) -> Tuple[RSChatGPT, List[Tuple[str, str]], List[str], str]:
    """重新加载 Agent"""
    try:
        if agent is not None:
            agent.initialize()
            tools = get_tool_list(agent)
            return agent, [], tools, "✅ Agent 已重新加载，对话历史已清空"
        else:
            new_agent = initialize_agent(gpt_name, openai_key, proxy_url, DEFAULT_LOAD_DICT)
            tools = get_tool_list(new_agent)
            return new_agent, [], tools, "✅ Agent 初始化成功"
    except Exception as e:
        return agent, [], [], f"❌ 重新加载失败: {str(e)}"


def copy_last_reply(chat_history: List[Tuple[str, str]]) -> str:
    """获取最后一次 AI 回复"""
    if not chat_history:
        return ""
    last_reply = chat_history[-1][1] if len(chat_history[-1]) > 1 else ""
    # 移除 emoji 前缀
    return last_reply.replace("🤖 ", "", 1)


# ==================== 构建界面 ====================

def build_interface(
    gpt_name: str,
    openai_key: str,
    proxy_url: str,
    enable_query_optimization: bool = False
) -> gr.Blocks:
    """构建 Gradio Web 界面"""
    
    # 使用全局变量存储 Agent（避免 deepcopy 问题）
    global_agent = {"instance": None, "tools": []}
    
    # 初始化 Agent
    try:
        agent = initialize_agent(gpt_name, openai_key, proxy_url, DEFAULT_LOAD_DICT, enable_query_optimization)
        global_agent["instance"] = agent
        global_agent["tools"] = get_tool_list(agent)
    except Exception as e:
        print(f"警告: 初始化 Agent 失败，将在运行时重试: {e}")
        global_agent["instance"] = None
        global_agent["tools"] = []
    
    # 创建界面
    with gr.Blocks(title="遥感 Agent 控制台", css=CUSTOM_CSS) as app:
        
        # 标题区
        with gr.Row(elem_id="title-container"):
            with gr.Column():
                gr.HTML('<div id="main-title">🛰️ 遥感 Agent 控制台</div>')
                gr.HTML('<div id="title-highlight"></div>')
                gr.HTML('<div id="subtitle">支持图文上传、多轮对话、工具自选</div>')
        
        # 状态变量
        chat_history_state = gr.State([])
        current_image_state = gr.State(None)
        second_image_state = gr.State(None)
        
        # 主布局
        with gr.Row(elem_id="main-container"):
            # 左侧控制面板
            with gr.Column(scale=1.5):
                with gr.Group(elem_classes=["card"]):
                    gr.Markdown("### 📤 图片上传")
                    gr.Markdown("💡 *单图任务只需上传图片1；变化检测需上传图片1和2*")
                    with gr.Row():
                        with gr.Column(scale=1):
                            gr.Markdown("**图片 1** (主图/变化前)")
                            image_upload_1 = gr.Image(
                                type="filepath",
                                label="",
                                elem_classes=["upload-area"],
                                show_label=False,
                                height=140
                            )
                        with gr.Column(scale=1):
                            gr.Markdown("**图片 2** (对比/变化后)")
                            image_upload_2 = gr.Image(
                                type="filepath",
                                label="",
                                elem_classes=["upload-area"],
                                show_label=False,
                                height=140
                            )
                    upload_status = gr.Textbox(
                        label="",
                        show_label=False,
                        interactive=False,
                        lines=2,
                        elem_classes=["status-text"]
                    )
                
                with gr.Group(elem_classes=["card"]):
                    gr.Markdown("### 🛠️ 工具选择")
                    tool_checkboxes = gr.CheckboxGroup(
                        choices=global_agent["tools"],
                        value=global_agent["tools"],
                        label="",
                        show_label=False,
                        elem_classes=["tool-checkbox"]
                    )
                
                with gr.Group(elem_classes=["card"]):
                    gr.Markdown("### 🔄 控制面板")
                    reload_btn = gr.Button(
                        "🔄 重新加载 Agent",
                        elem_classes=["primary-btn"]
                    )
                    reload_status = gr.Textbox(
                        label="",
                        show_label=False,
                        interactive=False,
                        lines=1,
                        elem_classes=["status-text"]
                    )
            
            # 中央对话区
            with gr.Column(scale=3):
                with gr.Group(elem_classes=["card"]):
                    gr.Markdown("### 💬 对话窗口")
                    chatbot = gr.Chatbot(
                        label="",
                        show_label=False,
                        height=520,
                        elem_classes=["chatbot-container"]
                    )
                    
                    with gr.Row():
                        user_input = gr.Textbox(
                            label="",
                            placeholder="请输入指令或问题…",
                            show_label=False,
                            lines=1,
                            scale=9,
                            elem_classes=["input-box"]
                        )
                        send_btn = gr.Button(
                            "➤",
                            scale=1,
                            elem_classes=["send-btn"]
                        )
                    
                    copy_btn = gr.Button(
                        "📋 复制最后一次回复",
                        elem_classes=["ghost-btn"]
                    )
                    copy_output = gr.Textbox(
                        label="复制内容",
                        interactive=False,
                        lines=2,
                        visible=False
                    )
        
        # 事件绑定
        
        # 图片 1 上传
        image_upload_1.change(
            fn=lambda file, history, img_path: handle_image_upload(
                file, global_agent["instance"], history, img_path
            ),
            inputs=[image_upload_1, chat_history_state, current_image_state],
            outputs=[current_image_state, chat_history_state, upload_status]
        ).then(
            fn=lambda history: history,
            inputs=[chat_history_state],
            outputs=[chatbot]
        )
        
        # 图片 2 上传
        image_upload_2.change(
            fn=lambda file, history, img_path: handle_image_upload(
                file, global_agent["instance"], history, img_path
            ),
            inputs=[image_upload_2, chat_history_state, second_image_state],
            outputs=[second_image_state, chat_history_state, upload_status]
        ).then(
            fn=lambda history: history,
            inputs=[chat_history_state],
            outputs=[chatbot]
        )
        
        # 发送消息（按钮）
        send_btn.click(
            fn=lambda txt, history, img1, img2, tools: handle_text_input(
                txt, global_agent["instance"], history, img1, img2, tools
            ),
            inputs=[user_input, chat_history_state, current_image_state, second_image_state, tool_checkboxes],
            outputs=[chat_history_state, user_input]
        ).then(
            fn=lambda history: history,
            inputs=[chat_history_state],
            outputs=[chatbot]
        )
        
        # 发送消息（回车）
        user_input.submit(
            fn=lambda txt, history, img1, img2, tools: handle_text_input(
                txt, global_agent["instance"], history, img1, img2, tools
            ),
            inputs=[user_input, chat_history_state, current_image_state, second_image_state, tool_checkboxes],
            outputs=[chat_history_state, user_input]
        ).then(
            fn=lambda history: history,
            inputs=[chat_history_state],
            outputs=[chatbot]
        )
        
        # 重新加载 Agent
        def _reload_wrapper():
            agent, history, tools, status = reload_agent(
                global_agent["instance"], gpt_name, openai_key, proxy_url
            )
            global_agent["instance"] = agent
            global_agent["tools"] = tools
            return history, tools, status
        
        reload_btn.click(
            fn=_reload_wrapper,
            inputs=[],
            outputs=[chat_history_state, tool_checkboxes, reload_status]
        ).then(
            fn=lambda history: history,
            inputs=[chat_history_state],
            outputs=[chatbot]
        )
        
        # 复制最后回复
        copy_btn.click(
            fn=copy_last_reply,
            inputs=[chat_history_state],
            outputs=[copy_output]
        ).then(
            fn=lambda: gr.update(visible=True),
            outputs=[copy_output]
        )
    
    return app


# ==================== 主程序入口 ====================

def main():
    """主程序入口"""
    parser = argparse.ArgumentParser(description="遥感 Agent Web UI")
    parser.add_argument(
        '--openai_key',
        type=str,
        default="sk-kQ11Ptt3RYbeTj7zBVSADbqXth7mA7Jj5dEmaWgtYiO04zdu",
        help='OpenAI API Key'
    )
    parser.add_argument(
        '--gpt_name',
        type=str,
        default="gpt-3.5-turbo",
        help='GPT 模型名称'
    )
    parser.add_argument(
        '--proxy_url',
        type=str,
        default="https://api.chatanywhere.tech",
        help='OpenAI API 代理 URL'
    )
    parser.add_argument(
        '--listen',
        type=str,
        default="0.0.0.0",
        help='监听地址'
    )
    parser.add_argument(
        '--port',
        type=int,
        default=7860,
        help='监听端口'
    )
    parser.add_argument(
        '--share',
        action='store_true',
        help='是否生成公共分享链接'
    )
    parser.add_argument(
        '--enable_query_optimization',
        action='store_true',
        help='启用 Promptomatix 查询优化'
    )
    
    args = parser.parse_args()
    
    print("=" * 60)
    print("🚀 正在启动遥感 Agent Web UI...")
    print("=" * 60)
    
    app = build_interface(
        gpt_name=args.gpt_name,
        openai_key=args.openai_key,
        proxy_url=args.proxy_url,
        enable_query_optimization=args.enable_query_optimization
    )
    
    print("\n✓ 界面构建完成，正在启动服务器...")
    print(f"  - 监听地址: {args.listen}:{args.port}")
    print(f"  - 分享链接: {'启用' if args.share else '禁用'}")
    print(f"  - 模型: {args.gpt_name}")
    print("=" * 60)
    
    try:
        app.launch(
            server_name=args.listen,
            server_port=args.port,
            share=args.share,
            inbrowser=True,
            show_error=True
        )
    except KeyboardInterrupt:
        print("\n\n👋 正在关闭服务器...")
        print("✓ 服务器已关闭")
    except Exception as e:
        print(f"\n❌ 启动失败: {e}")
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
