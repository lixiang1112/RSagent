# 测试结果文件格式说明

## 概述

`result/` 目录只保存测试结果文件，不再保存输入图片。所有结果文件使用统一的命名规则：`q{ID:03d}_{ToolType}_result.{ext}`

## 各工具结果格式

### 1. ChangeDetection (变化检测)

**输出文件**: `q{ID}_ChangeDetection_result.png`

**内容**: 水平拼接的3张图
- 左: Before (变化前)
- 中: After (变化后)  
- 右: Changes (变化mask，白色=变化区域)

**特点**:
- 一张图包含完整的对比信息
- 带有文字标注 "Before", "After", "Changes"
- 尺寸: 原图宽度×3

**示例**:
```
q001_ChangeDetection_result.png  (393K)
[Before图 | After图 | Mask图]
```

---

### 2. EdgeDetection (边缘检测)

**输出文件**: `q{ID}_EdgeDetection_result.png`

**内容**: 边缘检测结果图
- 黑白二值图
- 白色线条 = 检测到的边缘
- 黑色区域 = 非边缘区域

**特点**:
- Canny边缘检测算法
- 清晰的边缘轮廓

**示例**:
```
q003_EdgeDetection_result.png  (13K)
```

---

### 3. ImageCaptioning (图像描述)

**输出文件**: `q{ID}_ImageCaptioning_result.txt`

**内容**: 纯文本图像描述

**格式**:
```
A satellite image of an aerial view of the site.
```

**特点**:
- 只包含描述文字
- 无调试信息
- 无路径信息

---

### 4. SceneClassification (场景分类)

**输出文件**: `q{ID}_SceneClassification_result.txt`

**内容**: 格式化的分类结果

**格式**:
```
BareLand: 85.87%
Playground: 2.64%
Mountain: 1.23%
```

**特点**:
- 每行一个类别
- 按概率从高到低排序
- 最多显示前3个类别

---

### 5. ObjectCounting (目标计数)

**输出文件**: `q{ID}_ObjectCounting_result.txt`

**内容**: 目标数量统计

**格式**:
```
检测到 15 个目标
```

**特殊情况**:
- 如果类别不支持: "该类别不被模型支持，无法计数"
- 如果提取失败: "目标计数结果提取失败"

---

### 6. ObjectDetection (目标检测)

**输出文件**: 
- `q{ID}_ObjectDetection_result.png` (带边界框的结果图)
- `q{ID}_ObjectDetection_result.txt` (坐标文件)

**图像内容**: 
- 原图 + 标注的边界框
- 每个目标用矩形框标出

**文本格式**:
```
x1, y1, x2, y2, class_name
117, 172, 143, 190, swimming pool
234, 156, 267, 189, car
```

**特殊情况**:
- 如果未检测到目标，不生成结果文件

---

## 完整示例

### 测试6个问题后的result目录

```
result/
├── q121_ChangeDetection_result.png      (393K) - 拼接图
├── q122_EdgeDetection_result.png        (13K)  - 边缘图
├── q123_ImageCaptioning_result.txt      (63B)  - 图像描述
├── q124_ObjectCounting_result.txt       (42B)  - 计数结果
├── q125_ObjectDetection_result.png      (如果检测到目标)
├── q125_ObjectDetection_result.txt      (如果检测到目标)
└── q126_SceneClassification_result.txt  (30B)  - 分类结果
```

---

## 与原始数据的关系

### 输入图片位置
输入图片**不会**被复制到result目录，它们保留在原始位置：
```
/root/autodl-tmp/datasets/LEVIR-MCI-dataset/images/...
```

### 查找对应关系
通过 `RSquestion.json` 文件可以找到每个问题ID对应的输入图片路径：
```json
{
  "id": 121,
  "query": "对比这两个时期的影像，找出哪些区域发生了变化。",
  "tool": "ChangeDetection",
  "image": [
    "/root/autodl-tmp/datasets/.../train_000040.png",
    "/root/autodl-tmp/datasets/.../train_000040.png"
  ]
}
```

---

## 优势

1. **空间节省**: 不复制输入图片，节省大量存储空间
2. **结果清晰**: 每个文件只包含核心结果信息
3. **易于查看**: 
   - 变化检测：一张图看清所有对比
   - 文本结果：直接打开txt文件即可
4. **命名统一**: 所有文件都包含问题ID，便于追溯

---

## 查看结果

### 查看所有文本结果
```bash
cat result/*.txt
```

### 查看特定问题的结果
```bash
ls result/q121*
```

### 查看所有图像结果
```bash
ls -lh result/*.png
```

### 在Python中读取结果
```python
# 读取文本结果
with open('result/q123_ImageCaptioning_result.txt', 'r') as f:
    description = f.read()
    print(description)

# 读取图像结果
from PIL import Image
img = Image.open('result/q121_ChangeDetection_result.png')
img.show()
```

