# 图片文件命名规范

## 命名格式

### 1. 单图输入任务
适用于：ImageCaptioning, SceneClassification, ObjectDetection, ObjectCounting, EdgeDetection

**输入图片**：
```
q{问题ID}_{工具类型}.png
```

示例：
- `q002_ObjectCounting.png` - 问题2的输入图片
- `q015_EdgeDetection.png` - 问题15的输入图片
- `q120_ImageCaptioning.png` - 问题120的输入图片

### 2. 双图输入任务（变化检测）
适用于：ChangeDetection

**输入图片**：
```
q{问题ID}_ChangeDetection_before.png  # 变化前
q{问题ID}_ChangeDetection_after.png   # 变化后
```

示例：
- `q001_ChangeDetection_before.png` - 问题1的变化前图片
- `q001_ChangeDetection_after.png` - 问题1的变化后图片

### 3. 结果图片（由工具自动生成）

**边缘检测结果**：
```
{随机前缀}_edge_q{问题ID}.png
```
示例：`d3a8_edge_q122.png`

**变化检测结果**：
```
{随机前缀}_change_detection_q{问题ID}_before.png
```
示例：`119d_change_detection_q121_before.png`

**目标检测结果**：
```
{随机前缀}_detection_{目标类型}_q{问题ID}.png
{随机前缀}_detection_{目标类型}_q{问题ID}.txt  # 坐标文件
```
示例：
- `6277_detection_airplanes_q005.png` - 检测结果图
- `6277_detection_airplanes_q005.txt` - 边界框坐标

## 坐标文件格式

目标检测的txt文件格式：
```
x1, y1, x2, y2, class_name
```

示例：
```
117, 172, 143, 190, swimming pool
```
表示检测到一个对象，边界框从(117,172)到(143,190)，类别为swimming pool

## 文件组织示例

```
image/
├── q001_ChangeDetection_before.png       # 问题1输入（变化前）
├── q001_ChangeDetection_after.png        # 问题1输入（变化后）
├── 119d_change_detection_q001.png        # 问题1结果
├── q002_ObjectCounting.png               # 问题2输入
├── q003_EdgeDetection.png                # 问题3输入
├── d3a8_edge_q003.png                    # 问题3结果
├── q005_ObjectDetection.png              # 问题5输入
├── 6277_detection_airplanes_q005.png     # 问题5结果图
├── 6277_detection_airplanes_q005.txt     # 问题5坐标文件
└── ...
```

## 命名优势

1. **可追溯性**：通过文件名直接知道问题ID和工具类型
2. **清晰区分**：变化检测的before/after一目了然
3. **易于管理**：按问题ID排序，方便查找
4. **结果关联**：结果文件名包含问题ID，便于对应
