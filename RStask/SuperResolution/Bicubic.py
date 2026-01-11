from PIL import Image
import cv2
import numpy as np

class BicubicSuperResolution:
    """基于双三次插值的超分辨率算法"""
    def __init__(self):
        print("Initializing BicubicSuperResolution")
        self.scale_factor = 2  # 默认放大2倍
        
    def inference(self, inputs, new_image_name, scale=None):
        """执行超分辨率处理
        
        Args:
            inputs: 输入图像路径
            new_image_name: 输出图像路径
            scale: 放大倍数，默认为2
        """
        if scale is not None:
            self.scale_factor = scale
            
        image = Image.open(inputs)
        img = np.array(image)
        
        # 获取原始尺寸
        h, w = img.shape[:2]
        new_h = int(h * self.scale_factor)
        new_w = int(w * self.scale_factor)
        
        # 使用双三次插值进行超分辨率
        result = cv2.resize(img, (new_w, new_h), interpolation=cv2.INTER_CUBIC)
        
        # 应用锐化滤波器增强细节
        kernel = np.array([[-1, -1, -1],
                          [-1,  9, -1],
                          [-1, -1, -1]]) / 1.0
        result = cv2.filter2D(result, -1, kernel)
        
        # 确保像素值在有效范围内
        result = np.clip(result, 0, 255).astype(np.uint8)
        
        # 保存结果
        result_image = Image.fromarray(result)
        result_image.save(new_image_name)
        
        print(f"\nProcessed SuperResolution, Input Image: {inputs}, Output Image: {new_image_name}, Scale: {self.scale_factor}x")
        return None

