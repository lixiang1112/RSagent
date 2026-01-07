# result 目录说明

## 目录结构

`result/` 目录统一存储所有测试的输入和输出文件，包括：
- 输入图片
- 结果图片（EdgeDetection, ChangeDetection, ObjectDetection）
- 结果文本（ImageCaptioning, SceneClassification, ObjectCounting）

## 文件命名规则

### 1. 输入图片

#### 单图任务
```
q{ID:03d}_{ToolType}.png
```
示例：
- `q001_EdgeDetection.png`
- `q005_ObjectDetection.png`
- `q123_ImageCaptioning.png`

#### 变化检测（双图任务）
```
q{ID:03d}_ChangeDetection_before.png
q{ID:03d}_ChangeDetection_after.png
```
示例：
- `q001_ChangeDetection_before.png`
- `q001_ChangeDetection_after.png`

### 2. 结果文件

#### 图像结果（EdgeDetection, ChangeDetection, ObjectDetection）
```
{随机4位}_{func_name}_q{ID:03d}.png
```
示例：
- `a8e2_edge_q122.png` (边缘检测结果)
- `74d5_change_detection_q121.png` (变化检测mask)
- `xxxx_detection_airplanes_q005.png` (目标检测结果)

**说明**：
- 随机4位前缀由系统自动生成
- `func_name` 表示功能类型：`edge`, `change_detection`, `detection_*`
- 通过 `q{ID:03d}` 可以追溯到原始问题

#### 文本结果（ImageCaptioning, SceneClassification, ObjectCounting）
```
q{ID:03d}_{ToolType}_result.txt
```
示例：
- `q123_ImageCaptioning_result.txt`
- `q124_ObjectCounting_result.txt`
- `q126_SceneClassification_result.txt`

**文件内容格式**：
```
问题ID: 123
问题内容: 请描述一下这张卫星图像的主要内容是什么。
工具类型: ImageCaptioning
============================================================

结果:
[AI的文本输出结果]
```

#### 目标检测坐标文件（ObjectDetection）
```
{随机4位}_detection_{object_name}_q{ID:03d}.txt
```
示例：
- `6277_detection_airplanes_q005.txt`

**文件内容格式**：
```
x1, y1, x2, y2, class_name
117, 172, 143, 190, swimming pool
```

## 工具输出类型总览

| 工具 | 输出类型 | 文件示例 |
|------|---------|---------|
| **ChangeDetection** | 图像 | `74d5_change_detection_q121.png` |
| **EdgeDetection** | 图像 | `a8e2_edge_q122.png` |
| **ObjectDetection** | 图像+txt | `xxxx_detection_airplanes_q005.png`<br>`xxxx_detection_airplanes_q005.txt` |
| **ImageCaptioning** | 文本 | `q123_ImageCaptioning_result.txt` |
| **SceneClassification** | 文本 | `q126_SceneClassification_result.txt` |
| **ObjectCounting** | 文本 | `q124_ObjectCounting_result.txt` |

## 完整示例

### 问题121：变化检测
```
result/
├── q121_ChangeDetection_before.png      (输入：变化前)
├── q121_ChangeDetection_after.png       (输入：变化后)
└── 74d5_change_detection_q121.png       (输出：变化mask)
```

### 问题122：边缘检测
```
result/
├── q122_EdgeDetection.png               (输入)
└── a8e2_edge_q122.png                   (输出：边缘图)
```

### 问题123：图像描述
```
result/
├── q123_ImageCaptioning.png             (输入)
└── q123_ImageCaptioning_result.txt      (输出：文本描述)
```

### 问题005：目标检测（假设检测到目标）
```
result/
├── q005_ObjectDetection.png                  (输入)
├── xxxx_detection_airplanes_q005.png        (输出：带边界框的图)
└── xxxx_detection_airplanes_q005.txt        (输出：坐标文件)
```

## 查找技巧

### 按问题ID查找所有相关文件
```bash
ls -lh result/q121* result/*q121*
```

### 查找所有结果图
```bash
ls -lh result/*edge* result/*change_detection* result/*detection*
```

### 查找所有文本结果
```bash
ls -lh result/*_result.txt
```

### 查看某个问题的文本结果
```bash
cat result/q123_ImageCaptioning_result.txt
```

## 注意事项

1. **ObjectDetection** 只有在检测到目标时才会生成结果图和txt文件
2. **文本结果文件** 是新增功能，方便持久化保存文本输出工具的结果
3. 所有文件名都包含问题ID，便于追溯和分析
4. 随机前缀确保文件名唯一，避免覆盖

## 清理旧文件

如果需要清理测试文件：
```bash
# 清理特定问题的文件
rm -f result/q121* result/*q121*

# 清理所有测试生成的文件
rm -f result/q*
```
