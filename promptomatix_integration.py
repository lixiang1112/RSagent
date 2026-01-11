"""
Promptomatix 轻量级集成 - 仅用于动态查询优化
简化版：不依赖 dspy，直接使用 OpenAI API
"""
import sys
import os
from typing import Optional
import logging

class QueryOptimizer:
    """轻量级查询优化器（简化版）- 针对遥感图像处理优化"""
    
    def __init__(self, model_name="gpt-3.5-turbo", openai_key=None, proxy_url=None, enabled=True):
        self.enabled = enabled
        self.model_name = model_name
        self.openai_key = openai_key or os.getenv('OPENAI_API_KEY')
        self.proxy_url = proxy_url or "https://api.openai.com/v1"
        self.cache = {}  # 查询缓存
        self.cache_size = 100
        self.optimization_count = 0  # 统计优化次数
        self.skip_count = 0  # 统计跳过次数
        
        # 遥感领域专业术语映射
        self.rs_terminology = {
            # 边缘/边界相关
            '边界': 'edge',
            '边缘': 'edge',
            '轮廓': 'edge',
            
            # 检测方向相关
            '横向': 'horizontal',
            '水平': 'horizontal',
            '竖向': 'vertical',
            '垂直': 'vertical',
            '斜着': 'rotated',
            '旋转': 'rotated',
            '倾斜': 'rotated',
            
            # 图像质量相关
            '模糊': 'blurry',
            '噪声': 'noisy',
            '噪点': 'noisy',
            '清晰': 'clear',
            
            # 场景类型
            '区域': 'area',
            '地区': 'area',
            '类型': 'type',
            '场景': 'scene',
            
            # 目标相关
            '建筑': 'building',
            '房屋': 'building',
            '道路': 'road',
            '车辆': 'vehicle',
            '飞机': 'plane',
            '船': 'ship',
            
            # 颜色
            '绿色': 'green',
            '红色': 'red',
            '蓝色': 'blue',
            '白色': 'white',
            '黑色': 'black',
        }
        
        # 工具关键词映射（用于保持语义一致性）
        self.tool_keywords = {
            'EdgeDetection': ['边界', '边缘', '轮廓', 'edge', 'boundary', 'contour'],
            'ChangeDetection': ['变化', '不同', '对比', '差异', 'change', 'difference', 'compare'],
            'ObjectCounting': ['多少', '数量', '计数', 'count', 'number', 'how many'],
            'ObjectDetection': ['找出', '检测', '识别', 'detect', 'find', 'identify'],
            'ImageCaptioning': ['描述', '介绍', '说明', 'describe', 'caption', 'explain'],
            'SceneClassification': ['类型', '场景', '分类', 'type', 'scene', 'classify', 'category'],
            'CloudRemoval': ['云', '去云', 'cloud', 'remove cloud'],
            'SuperResolution': ['清晰', '分辨率', '放大', 'resolution', 'enhance', 'sharpen', 'clear'],
            'Denoising': ['噪声', '噪点', '去噪', 'noise', 'denoise', 'clean'],
            'HorizontalDetection': ['横向', '水平', 'horizontal'],
            'RotatedDetection': ['斜着', '旋转', '倾斜', 'rotated', 'tilted', 'angled'],
        }
        
        if self.enabled:
            try:
                from openai import OpenAI
                self.client = OpenAI(api_key=self.openai_key, base_url=self.proxy_url)
                print("✓ 查询优化器已启用（遥感领域专业版）")
            except ImportError as e:
                print(f"⚠️ OpenAI 导入失败，查询优化已禁用: {e}")
                self.enabled = False
    
    def _detect_intended_tool(self, query: str) -> Optional[str]:
        """检测查询意图对应的工具"""
        query_lower = query.lower()
        
        # 优先级检测：某些工具需要更精确的匹配
        # 1. 边缘检测（最高优先级，因为容易被误判为超分辨率）
        if any(kw in query_lower for kw in ['边界', '边缘', '轮廓']):
            return 'EdgeDetection'
        
        # 2. 旋转检测（高优先级）
        if any(kw in query_lower for kw in ['斜着', '旋转', '倾斜', 'rotated', 'tilted', 'angled']):
            return 'RotatedDetection'
        
        # 3. 横向检测
        if any(kw in query_lower for kw in ['横向', '水平', 'horizontal']):
            return 'HorizontalDetection'
        
        # 4. 去噪 vs 超分辨率（需要区分"模糊"的不同含义）
        if '模糊' in query_lower or 'blur' in query_lower:
            if any(kw in query_lower for kw in ['处理', '去噪', 'denoise', 'noise']):
                return 'Denoising'
            elif any(kw in query_lower for kw in ['清晰', '分辨率', 'clear', 'resolution', 'sharpen']):
                return 'SuperResolution'
        
        # 5. 其他工具按关键词匹配
        for tool, keywords in self.tool_keywords.items():
            if tool in ['EdgeDetection', 'RotatedDetection', 'HorizontalDetection', 'Denoising', 'SuperResolution']:
                continue  # 已经处理过
            for keyword in keywords:
                if keyword in query_lower:
                    return tool
        return None
    
    def _rule_based_optimize(self, query: str, intended_tool: Optional[str]) -> Optional[str]:
        """基于规则的优化（快速路径，避免API调用）"""
        if not intended_tool:
            return None
        
        # 提取图片路径（支持单个或多个，用逗号分隔）
        import re
        image_paths = re.findall(r'(/[^\s,]+\.(?:png|jpg|jpeg))', query)
        
        if len(image_paths) == 0:
            image_path_str = ""
        elif len(image_paths) == 1:
            image_path_str = f" at {image_paths[0]}"
        else:
            # 多个图片路径，用于 ChangeDetection
            image_path_str = f" {','.join(image_paths)}"
        
        # 基于工具类型生成优化查询
        # 注意：使用与工具名称完全匹配的动作描述，避免Agent误选工具
        templates = {
            'EdgeDetection': f"Use Edge Detection On Image{image_path_str}.",
            'ChangeDetection': f"Use Change Detection On Image Pair{image_path_str}." if len(image_paths) >= 2 else None,
            'ObjectCounting': None,  # 需要保留具体目标，使用LLM优化
            'ObjectDetection': None,  # 需要保留具体目标，使用LLM优化
            'ImageCaptioning': f"Get Photo Description of the image{image_path_str}.",
            'SceneClassification': f"Use Scene Classification for Remote Sensing Image{image_path_str}.",
            'CloudRemoval': f"Use Cloud Removal On Image{image_path_str}.",
            'SuperResolution': f"Use Super Resolution On Image{image_path_str}.",
            'Denoising': f"Use Denoising On Image{image_path_str}.",
            'HorizontalDetection': f"Use Horizontal Detection On Image{image_path_str}.",
            'RotatedDetection': f"Use Rotated Detection On Image{image_path_str}.",
        }
        
        return templates.get(intended_tool)
    
    def optimize_query(self, user_query: str, image_context: Optional[str] = None) -> str:
        """
        优化用户查询，使其更清晰和具体（针对遥感领域优化）
        
        Args:
            user_query: 用户原始查询
            image_context: 可选的图像上下文描述
            
        Returns:
            优化后的查询文本
        """
        if not self.enabled:
            return user_query
        
        # 跳过简单的问候语和确认语句
        simple_phrases = ['hi', 'hello', 'thanks', 'thank you', 'ok', 'yes', 'no', 'received', '好的', '谢谢', '收到']
        if user_query.lower().strip() in simple_phrases or len(user_query.strip()) < 3:
            self.skip_count += 1
            return user_query
        
        # 检查缓存
        cache_key = f"{user_query}_{image_context}"
        if cache_key in self.cache:
            print("✓ 使用缓存的优化结果")
            return self.cache[cache_key]
        
        # 检测意图工具
        intended_tool = self._detect_intended_tool(user_query)
        
        # 尝试基于规则的快速优化
        rule_based_result = self._rule_based_optimize(user_query, intended_tool)
        if rule_based_result:
            self.optimization_count += 1
            print(f"🔧 查询优化 (#{self.optimization_count}) [规则]:")
            print(f"   原始: {user_query}")
            print(f"   优化: {rule_based_result}")
            print(f"   意图: {intended_tool}")
            
            # 保存到缓存
            if len(self.cache) >= self.cache_size:
                self.cache.pop(next(iter(self.cache)))
            self.cache[cache_key] = rule_based_result
            return rule_based_result
        
        try:
            # 构建针对遥感领域的优化提示
            system_prompt = """You are a query optimization expert for remote sensing AI systems. 
Your task is to clarify and optimize user queries while PRESERVING the original semantic intent and technical terminology.

CRITICAL RULES for Remote Sensing Domain:
1. Edge/Boundary Detection:
   - "边界" or "边缘" → use "edge detection" (NOT "enhance sharpness" or "super resolution")
   - Example: "让边界更清晰" → "Detect edges in the image"

2. Direction-specific Detection:
   - "横向" → "horizontal detection"
   - "斜着" or "旋转" → "rotated detection" (NOT "tilted" or general "detect")
   - Example: "斜着的建筑" → "Detect rotated buildings"

3. Image Quality Enhancement:
   - "模糊" with "清晰" → "super resolution" (enhance clarity/resolution)
   - "模糊" with "处理" → "denoising" (remove noise)
   - Keep the distinction clear!

4. Terminology Mapping:
   - 边界/边缘 → edge (NOT boundary)
   - 斜着/旋转 → rotated (NOT tilted)
   - 横向 → horizontal
   - 描述 → describe/caption (NOT analyze)

5. Preserve Key Technical Terms:
   - Keep specific object types (buildings, roads, vehicles)
   - Keep color attributes (green, red, blue)
   - Keep spatial relationships (horizontal, vertical, rotated)

Guidelines:
- Keep the optimized query concise (one sentence)
- Translate Chinese to English while preserving technical meaning
- Use precise remote sensing terminology
- DO NOT change the intended tool/action"""

            # 构建用户提示，包含意图工具信息
            user_prompt = f"""Optimize this remote sensing task request:

User query: {user_query}"""
            
            if intended_tool:
                user_prompt += f"\nDetected intent: {intended_tool}"
            
            if image_context:
                user_prompt += f"\nImage context: {image_context}"
            
            user_prompt += "\n\nOptimized query (preserve the technical intent):"
            
            # 调用 OpenAI API
            response = self.client.chat.completions.create(
                model=self.model_name,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.1,  # 降低温度以获得更一致的结果
                max_tokens=150
            )
            
            optimized = response.choices[0].message.content.strip()
            
            # 验证优化结果是否保持了原始意图
            if intended_tool:
                optimized_tool = self._detect_intended_tool(optimized)
                if optimized_tool and optimized_tool != intended_tool:
                    print(f"⚠️ 优化改变了工具意图: {intended_tool} → {optimized_tool}，使用原查询")
                    self.skip_count += 1
                    return user_query
            
            # 如果优化结果太短，使用原查询
            if len(optimized) < 3:
                print(f"⚠️ 优化结果太短 (长度={len(optimized)})")
                self.skip_count += 1
                return user_query
            
            # 保存到缓存
            if len(self.cache) >= self.cache_size:
                self.cache.pop(next(iter(self.cache)))  # 移除最旧的
            self.cache[cache_key] = optimized
            
            self.optimization_count += 1
            print(f"🔧 查询优化 (#{self.optimization_count}):")
            print(f"   原始: {user_query}")
            print(f"   优化: {optimized}")
            if intended_tool:
                print(f"   意图: {intended_tool}")
            return optimized
            
        except Exception as e:
            print(f"⚠️ 查询优化失败，使用原查询: {e}")
            self.skip_count += 1
            return user_query
    
    def optimize_if_ambiguous(self, user_query: str, image_context: Optional[str] = None) -> str:
        """
        仅当查询模糊时才优化（更保守的策略）
        
        Args:
            user_query: 用户查询
            image_context: 图像上下文
            
        Returns:
            优化后的查询
        """
        if not self.enabled:
            return user_query
        
        # 对所有非简单问候语的查询都进行优化
        # 这样可以最大化看到优化效果
        return self.optimize_query(user_query, image_context)
    
    def get_stats(self):
        """获取统计信息"""
        return {
            'optimization_count': self.optimization_count,
            'skip_count': self.skip_count,
            'cache_size': len(self.cache)
        }

