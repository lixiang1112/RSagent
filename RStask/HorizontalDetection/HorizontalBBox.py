from PIL import Image, ImageDraw, ImageFont
import cv2
import numpy as np

class HorizontalBBoxDetection:
    """水平边界框检测算法（基于边缘检测和轮廓提取）"""
    def __init__(self):
        print("Initializing HorizontalBBoxDetection")
        self.min_area = 100  # 最小检测区域面积
        self.canny_low = 50
        self.canny_high = 150
        
    def inference(self, inputs, new_image_name):
        """执行水平边界框检测
        
        Args:
            inputs: 输入图像路径
            new_image_name: 输出图像路径
        """
        image = Image.open(inputs)
        img = np.array(image)
        
        # 转换为灰度图
        if len(img.shape) == 3:
            gray = cv2.cvtColor(img, cv2.COLOR_RGB2GRAY)
        else:
            gray = img
        
        # 高斯模糊
        blurred = cv2.GaussianBlur(gray, (5, 5), 0)
        
        # Canny边缘检测
        edges = cv2.Canny(blurred, self.canny_low, self.canny_high)
        
        # 形态学操作，连接边缘
        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (5, 5))
        closed = cv2.morphologyEx(edges, cv2.MORPH_CLOSE, kernel)
        
        # 查找轮廓
        contours, _ = cv2.findContours(closed, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        # 在原图上绘制水平边界框
        result_img = image.copy()
        draw = ImageDraw.Draw(result_img)
        
        bbox_count = 0
        for contour in contours:
            area = cv2.contourArea(contour)
            if area < self.min_area:
                continue
            
            # 获取水平边界框
            x, y, w, h = cv2.boundingRect(contour)
            
            # 绘制矩形框
            draw.rectangle([x, y, x+w, y+h], outline='red', width=2)
            
            # 添加标签
            label = f"Object {bbox_count+1}"
            try:
                font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 12)
            except:
                font = ImageFont.load_default()
            draw.text((x, y-15), label, fill='red', font=font)
            
            bbox_count += 1
        
        # 保存结果
        result_img.save(new_image_name)
        
        print(f"\nProcessed HorizontalDetection, Input Image: {inputs}, Output Image: {new_image_name}, Detected: {bbox_count} objects")
        return None

