from PIL import Image
import cv2
import numpy as np

class DarkChannelCloudRemoval:
    """基于暗通道先验的云雾去除算法"""
    def __init__(self):
        print("Initializing DarkChannelCloudRemoval")
        self.omega = 0.95  # 去雾程度
        self.t0 = 0.1      # 最小透射率
        self.radius = 15   # 暗通道窗口半径
        
    def get_dark_channel(self, img, size=15):
        """计算暗通道"""
        b, g, r = cv2.split(img)
        min_img = cv2.min(cv2.min(r, g), b)
        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (size, size))
        dark = cv2.erode(min_img, kernel)
        return dark
    
    def get_atmosphere(self, img, dark):
        """估计大气光值"""
        h, w = img.shape[:2]
        num_pixels = h * w
        num_brightest = int(max(num_pixels * 0.001, 1))
        
        dark_vec = dark.reshape(num_pixels)
        img_vec = img.reshape(num_pixels, 3)
        
        indices = dark_vec.argsort()[-num_brightest:]
        brightest_pixels = img_vec[indices]
        
        atmosphere = np.mean(brightest_pixels, axis=0)
        return atmosphere
    
    def get_transmission(self, img, atmosphere):
        """估计透射率"""
        norm_img = np.empty_like(img, dtype=np.float64)
        for i in range(3):
            norm_img[:, :, i] = img[:, :, i] / atmosphere[i]
        
        transmission = 1 - self.omega * self.get_dark_channel(norm_img, self.radius)
        return transmission
    
    def guided_filter(self, I, p, r, eps):
        """导向滤波"""
        mean_I = cv2.boxFilter(I, cv2.CV_64F, (r, r))
        mean_p = cv2.boxFilter(p, cv2.CV_64F, (r, r))
        mean_Ip = cv2.boxFilter(I * p, cv2.CV_64F, (r, r))
        cov_Ip = mean_Ip - mean_I * mean_p
        
        mean_II = cv2.boxFilter(I * I, cv2.CV_64F, (r, r))
        var_I = mean_II - mean_I * mean_I
        
        a = cov_Ip / (var_I + eps)
        b = mean_p - a * mean_I
        
        mean_a = cv2.boxFilter(a, cv2.CV_64F, (r, r))
        mean_b = cv2.boxFilter(b, cv2.CV_64F, (r, r))
        
        q = mean_a * I + mean_b
        return q
    
    def recover(self, img, transmission, atmosphere):
        """恢复去云图像"""
        result = np.empty_like(img, dtype=np.float64)
        transmission = np.maximum(transmission, self.t0)
        
        for i in range(3):
            result[:, :, i] = (img[:, :, i] - atmosphere[i]) / transmission + atmosphere[i]
        
        return result

    def inference(self, inputs, new_image_name):
        """执行云雾去除"""
        image = Image.open(inputs)
        img = np.array(image).astype(np.float64) / 255.0
        
        # 计算暗通道
        dark = self.get_dark_channel(img, self.radius)
        
        # 估计大气光
        atmosphere = self.get_atmosphere(img, dark)
        
        # 估计透射率
        transmission = self.get_transmission(img, atmosphere)
        
        # 使用导向滤波优化透射率
        gray = cv2.cvtColor((img * 255).astype(np.uint8), cv2.COLOR_RGB2GRAY).astype(np.float64) / 255.0
        transmission = self.guided_filter(gray, transmission, r=60, eps=0.0001)
        
        # 恢复图像
        result = self.recover(img, transmission, atmosphere)
        
        # 转换回uint8并保存
        result = np.clip(result * 255, 0, 255).astype(np.uint8)
        result_image = Image.fromarray(result)
        result_image.save(new_image_name)
        
        print(f"\nProcessed CloudRemoval, Input Image: {inputs}, Output Image: {new_image_name}")
        return None

