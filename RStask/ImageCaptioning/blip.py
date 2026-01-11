import torch
import os
from PIL import Image
from transformers import  BlipProcessor, BlipForConditionalGeneration

class BLIP:
    def __init__(self, device):
        self.device = device
        self.torch_dtype = torch.float16 if 'cuda' in device else torch.float32
        
        # 本地模型路径
        local_model_path = "/root/autodl-tmp/blip"
        
        # 检查本地模型是否存在
        model_files = ['config.json', 'pytorch_model.bin', 'tokenizer.json']
        local_model_exists = all(
            os.path.exists(os.path.join(local_model_path, f)) for f in model_files
        )
        
        if local_model_exists:
            # 从本地加载模型
            print(f"从本地路径加载模型: {local_model_path}")
            self.processor = BlipProcessor.from_pretrained(local_model_path, local_files_only=True)
            self.model = BlipForConditionalGeneration.from_pretrained(
                local_model_path, 
                torch_dtype=self.torch_dtype,
                local_files_only=True
            ).to(self.device)
        else:
            # 本地模型不存在，尝试在线下载
            print(f"本地模型不存在，尝试在线下载...")
            model_name = "Salesforce/blip-image-captioning-base"
            
            # 设置 Hugging Face 镜像源
            if 'HF_ENDPOINT' not in os.environ:
                os.environ['HF_ENDPOINT'] = 'https://hf-mirror.com'
            
            try:
                self.processor = BlipProcessor.from_pretrained(
                    model_name, 
                    cache_dir=local_model_path
                )
                self.model = BlipForConditionalGeneration.from_pretrained(
                    model_name, 
                    torch_dtype=self.torch_dtype,
                    cache_dir=local_model_path
                ).to(self.device)
            except Exception as e:
                # 如果镜像源失败，尝试使用官方源
                if 'hf-mirror.com' in os.environ.get('HF_ENDPOINT', ''):
                    print(f"镜像源下载失败，尝试使用官方源: {e}")
                    os.environ['HF_ENDPOINT'] = 'https://huggingface.co'
                    self.processor = BlipProcessor.from_pretrained(
                        model_name,
                        cache_dir=local_model_path
                    )
                    self.model = BlipForConditionalGeneration.from_pretrained(
                        model_name, 
                        torch_dtype=self.torch_dtype,
                        cache_dir=local_model_path
                    ).to(self.device)
                else:
                    raise
    def inference(self, image_path):
        inputs = self.processor(Image.open(image_path), return_tensors="pt").to(self.device, self.torch_dtype)
        out = self.model.generate(**inputs, max_new_tokens=50)
        captions = 'A satellite image of ' + self.processor.decode(out[0], skip_special_tokens=True)
        print(f"\nProcessed ImageCaptioning, Input Image: {image_path}, Output Text: {captions}")
        return captions