# 工具输出类型说明

## 生成可视化结果图的工具

### 1. ChangeDetection (变化检测) ✅
**输入**：2张图片（before, after）
**输出**：
- 变化检测mask图（白色=变化区域，黑色=未变化）
- 统计信息：变化像素数量和百分比

**文件示例**：
```
q001_ChangeDetection_before.png    (输入)
q001_ChangeDetection_after.png     (输入)
xxxx_change_detection_q001.png     (结果mask)
```

### 2. EdgeDetection (边缘检测) ✅
**输入**：1张图片
**输出**：
- 边缘检测结果图（Canny边缘检测）
- 白色线条表示检测到的边缘

**文件示例**：
```
q003_EdgeDetection.png        (输入)
xxxx_edge_q003.png            (边缘结果)
```

### 3. ObjectDetection (目标检测) ⚠️
**输入**：1张图片 + 目标描述
**输出**：
- 如果检测到目标：生成带边界框的结果图 + txt坐标文件
- 如果未检测到：返回None，不生成图片

**文件示例**（检测到目标时）：
```
q005_ObjectDetection.png                  (输入)
xxxx_detection_airplanes_q005.png        (结果图)
xxxx_detection_airplanes_q005.txt        (坐标文件)
```

**坐标文件格式**：
```
x1, y1, x2, y2, class_name
117, 172, 143, 190, swimming pool
```

## 仅返回文本结果的工具

### 4. ImageCaptioning (图像描述) ✗
**输入**：1张图片
**输出**：文本描述（不生成图片）

**示例输出**：
```
"A satellite image of an aerial view of the site"
```

### 5. SceneClassification (场景分类) ✗
**输入**：1张图片
**输出**：场景类别和概率（不生成图片）

**示例输出**：
```
"image.png has 95.95% probability being Mountain and 0.76% probability being Church."
```

### 6. ObjectCounting (目标计数) ✗
**输入**：1张图片 + 目标类别
**输出**：数量统计（不生成图片）

**示例输出**：
```
"There are 15 cars in the image"
```

## 总结

| 工具 | 生成结果图 | 输出类型 |
|------|-----------|---------|
| ChangeDetection | ✅ 是 | 变化mask图 |
| EdgeDetection | ✅ 是 | 边缘检测图 |
| ObjectDetection | ⚠️ 条件 | 检测到目标时生成 |
| ImageCaptioning | ❌ 否 | 文本描述 |
| SceneClassification | ❌ 否 | 类别+概率 |
| ObjectCounting | ❌ 否 | 数量统计 |

## 注意事项

1. **ObjectDetection** 只有在成功检测到目标时才会生成结果图
2. **文本结果工具**（ImageCaptioning, SceneClassification, ObjectCounting）的输出会记录在终端和test_details.txt中
3. 所有结果图的文件名都包含问题ID（如 `q001`, `q122`），便于追溯
