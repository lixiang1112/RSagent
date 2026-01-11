from PIL import Image
import cv2
import numpy as np

class NonLocalMeansDenoising:
    """基于非局部均值的去噪算法"""
    def __init__(self):
        print("Initializing NonLocalMeansDenoising")
        self.h = 10  # 滤波强度，值越大去噪效果越强但会损失更多细节
        self.template_window_size = 7  # 模板窗口大小
        self.search_window_size = 21   # 搜索窗口大小
        
    def inference(self, inputs, new_image_name):
        """执行图像去噪
        
        Args:
            inputs: 输入图像路径
            new_image_name: 输出图像路径
        """
        image = Image.open(inputs)
        img = np.array(image)
        
        # 判断是灰度图还是彩色图
        if len(img.shape) == 2:
            # 灰度图去噪
            result = cv2.fastNlMeansDenoising(
                img, 
                None, 
                h=self.h,
                templateWindowSize=self.template_window_size,
                searchWindowSize=self.search_window_size
            )
        else:
            # 彩色图去噪
            result = cv2.fastNlMeansDenoisingColored(
                img,
                None,
                h=self.h,
                hColor=self.h,
                templateWindowSize=self.template_window_size,
                searchWindowSize=self.search_window_size
            )
        
        # 保存结果
        result_image = Image.fromarray(result)
        result_image.save(new_image_name)
        
        print(f"\nProcessed Denoising, Input Image: {inputs}, Output Image: {new_image_name}")
        return None

