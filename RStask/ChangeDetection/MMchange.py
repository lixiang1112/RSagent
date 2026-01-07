import sys
import os
import torch
import torch.nn.functional as F
import numpy as np
from PIL import Image
import clip
import cv2

# 添加 MMchange 路径
MMCHANGE_PATH = '/root/MMchange-main'
sys.path.insert(0, MMCHANGE_PATH)

# 导入 MMchange 相关模块
import Transforms as myTransforms
from models.model import BaseNet, BaseNet_Hybrid


class MMChangeDetection:
    """变化检测模型封装类"""
    
    def __init__(self, device):
        """
        初始化变化检测模型
        
        Args:
            device: 设备类型，如 'cuda:0' 或 'cpu'
        """
        print(f"正在初始化变化检测模型到设备 {device}...")
        self.device = device
        
        # 模型配置
        self.model_path = '/root/MMchange-main/results_change_caption_transfer_LEVIR_iter_40000_lr_0.0005/best_model.pth'
        self.model_arch = 'basenet'  # 或 'basenet_hybrid'
        self.use_change_caption = True
        self.img_size = 256
        
        # 检查模型文件是否存在
        if not os.path.exists(self.model_path):
            raise FileNotFoundError(f"模型文件不存在: {self.model_path}")
        
        # 初始化变化检测模型
        print("加载变化检测模型...")
        if self.model_arch == 'basenet':
            self.model = BaseNet(3, 1, use_change_caption=self.use_change_caption)
        elif self.model_arch == 'basenet_hybrid':
            self.model = BaseNet_Hybrid(3, 1)
        else:
            raise ValueError(f"未知的模型架构: {self.model_arch}")
        
        # 加载模型权重
        state_dict = torch.load(self.model_path, map_location='cpu')
        self.model.load_state_dict(state_dict)
        
        if 'cuda' in device:
            self.model = self.model.cuda()
        
        self.model.eval()
        print("变化检测模型加载成功！")
        
        # 加载 CLIP 模型用于文本编码
        print("加载 CLIP 模型...")
        self.clip_model, _ = clip.load("ViT-B/32", device=device)
        print("CLIP 模型加载成功！")
        
        # 数据预处理配置（与训练时保持一致）
        mean = [0.406, 0.456, 0.485, 0.406, 0.456, 0.485]
        std = [0.225, 0.224, 0.229, 0.225, 0.224, 0.229]
        self.transform = myTransforms.Compose([
            myTransforms.Normalize(mean=mean, std=std),
            myTransforms.Scale(self.img_size, self.img_size),
            myTransforms.ToTensor()
        ])
        
        print("变化检测模块初始化完成！")
    
    def preprocess_images(self, pre_image_path, post_image_path):
        """
        预处理图像对
        
        Args:
            pre_image_path: 前时相图像路径
            post_image_path: 后时相图像路径
        
        Returns:
            pre_img_tensor: 预处理后的前时相图像张量
            post_img_tensor: 预处理后的后时相图像张量
        """
        # 读取图像（使用 cv2，与训练时保持一致）
        import cv2
        pre_img = cv2.imread(pre_image_path)
        post_img = cv2.imread(post_image_path)
        
        # 拼接前后时相图像（沿通道维度，与 dataset.py 中保持一致）
        # pre_img: [H, W, 3], post_img: [H, W, 3] -> img: [H, W, 6]
        img = np.concatenate((pre_img, post_img), axis=2)
        
        # 创建虚拟的 label（二值标签）
        dummy_label = np.zeros((pre_img.shape[0], pre_img.shape[1]), dtype=np.float32)
        
        # 应用变换 (transform 接受 img 和 label 两个参数)
        transformed = self.transform(img, dummy_label)
        img_tensor = transformed[0]  # [C*2, H, W]，其中 C=3
        
        # 分离前后时相
        pre_img_tensor = img_tensor[0:3].unsqueeze(0)  # [1, 3, H, W]
        post_img_tensor = img_tensor[3:6].unsqueeze(0)  # [1, 3, H, W]
        
        return pre_img_tensor, post_img_tensor
    
    def encode_text(self, text):
        """
        使用 CLIP 编码文本
        
        Args:
            text: 文本描述（字符串或字符串列表）
        
        Returns:
            text_features: 文本特征张量
        """
        if isinstance(text, str):
            text = [text]
        
        text_tokens = clip.tokenize(text).to(self.device)
        with torch.no_grad():
            text_features = self.clip_model.encode_text(text_tokens)
        
        return text_features
    
    @torch.no_grad()
    def inference(self, pre_image_path, post_image_path, output_path, 
                  change_caption=None, caption_A=None, caption_B=None):
        """
        执行变化检测推理
        
        Args:
            pre_image_path: 前时相图像路径
            post_image_path: 后时相图像路径
            output_path: 输出结果图像路径
            change_caption: 变化描述文本（可选，默认为通用描述）
            caption_A: 前时相图像描述（可选）
            caption_B: 后时相图像描述（可选）
        
        Returns:
            result_text: 结果描述文本
        """
        # 预处理图像
        pre_img, post_img = self.preprocess_images(pre_image_path, post_image_path)
        
        # 移动到设备
        if 'cuda' in self.device:
            pre_img = pre_img.cuda()
            post_img = post_img.cuda()
        
        # 准备文本特征
        if change_caption is None:
            change_caption = "buildings have been constructed or demolished"
        
        change_text_features = self.encode_text(change_caption)
        change_text_features = change_text_features.float()
        
        if 'cuda' in self.device:
            change_text_features = change_text_features.cuda()
        
        # 准备前后时相文本特征（如果使用混合架构）
        text_A_features = None
        text_B_features = None
        
        if self.model_arch == 'basenet_hybrid' or (caption_A and caption_B):
            if caption_A is None:
                caption_A = "An aerial image"
            if caption_B is None:
                caption_B = "An aerial image"
            
            text_A_features = self.encode_text(caption_A).float()
            text_B_features = self.encode_text(caption_B).float()
            
            if 'cuda' in self.device:
                text_A_features = text_A_features.cuda()
                text_B_features = text_B_features.cuda()
        
        # 模型推理
        if self.model_arch == 'basenet_hybrid':
            output, _, _, _ = self.model(
                pre_img, post_img, change_text_features, text_A_features, text_B_features
            )
        else:
            if self.use_change_caption:
                output, _, _, _ = self.model(pre_img, post_img, change_text_features)
            else:
                output, _, _, _ = self.model(pre_img, post_img, text_A_features, text_B_features)
        
        # 二值化预测结果
        pred = torch.where(output > 0.5, torch.ones_like(output), torch.zeros_like(output))
        pred = pred.cpu().numpy()[0, 0]  # [H, W]
        
        # 读取原始图像用于可视化
        pre_img_raw = cv2.imread(pre_image_path)
        post_img_raw = cv2.imread(post_image_path)
        
        # 调整预测结果尺寸以匹配原始图像
        h, w = pre_img_raw.shape[:2]
        pred_resized = cv2.resize(pred, (w, h), interpolation=cv2.INTER_NEAREST)
        
        # 创建可视化结果
        # 将预测结果转换为彩色图像（红色表示变化区域）
        pred_vis = np.zeros((h, w, 3), dtype=np.uint8)
        pred_vis[pred_resized > 0.5] = [0, 0, 255]  # 变化区域用红色标记
        
        # 将变化区域叠加到后时相图像上
        alpha = 0.5
        result_vis = post_img_raw.copy().astype(np.float32)
        mask = pred_resized > 0.5
        # 使用 numpy 数组操作实现混合效果
        result_vis[mask] = (1 - alpha) * post_img_raw[mask] + alpha * pred_vis[mask]
        result_vis = result_vis.astype(np.uint8)
        
        # 拼接前时相、后时相和变化检测结果
        vis = np.hstack([
            cv2.resize(pre_img_raw, (w, h)),
            cv2.resize(post_img_raw, (w, h)),
            result_vis
        ])
        
        # 保存结果
        cv2.imwrite(output_path, vis)
        
        # 计算变化像素数量和比例
        total_pixels = h * w
        changed_pixels = np.sum(pred_resized > 0.5)
        change_ratio = changed_pixels / total_pixels * 100
        
        result_text = f"Change detection completed. Changed area: {change_ratio:.2f}% ({changed_pixels}/{total_pixels} pixels). Result saved to {output_path}"
        
        print(result_text)
        return result_text

