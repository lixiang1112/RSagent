# RSChatGPT 测试脚本说明

## 功能特点

### 1. 实时结果记录
每完成一个问题就立即写入CSV文件，无需等待所有测试完成。测试过程中可以随时查看进度。

### 2. 多文件输出

#### test_results.csv（表格结果）
清晰的表格形式，包含：
- 问题序号
- 问题内容
- Ground Truth Tool（正确答案）
- 实际调用Tool（模型实际调用的工具）
- 是否正确（✓ 或 ✗）

可用Excel、WPS等表格软件直接打开。

#### test_details.txt（详细日志）
记录每个问题的完整执行过程：
- Agent的推理过程（Thought, Action, Observation）
- 工具调用的详细信息
- 错误原因分析（如果判断错误）
- 异常堆栈跟踪（如果程序出错）

**用途**：分析为什么模型会调用错误的工具，理解模型的推理过程。

#### test_summary.json（统计汇总）
JSON格式的测试统计信息，便于程序化分析。

### 3. 智能工具提取

#### 提取策略
1. **优先级1**：从 `intermediate_steps` 提取第一个工具调用
2. **优先级2**：如果失败，从标准输出中解析工具调用

#### 关键原则：取第一个工具调用
在多工具调用场景中：
- **第一个工具调用**：反映模型对问题的主要理解和意图 ✓
- **后续工具调用**：通常是辅助或补救措施

**示例**：
```
问题："照片里有多少艘船？"
执行过程：
  1. Count object (船) - 主要任务 ← 这个才是判断依据
  2. Get Photo Description - 辅助（因为计数失败）
判断：ObjectCounting ✓
```

### 4. 健壮的错误处理
- 捕获agent执行异常
- 记录完整的错误信息和堆栈
- 多种解析方法确保不漏掉工具调用信息

## 使用方法

### 基本用法
```bash
cd /root/Remote-Sensing-ChatGPT
source /root/miniconda3/bin/activate mmchange
python test_rschatgpt.py
```

### 只测试部分数据
编辑 `test_rschatgpt.py`，找到这行：
```python
# questions = questions[:5]  # 只测试前5个
```
取消注释即可只测试前5个问题。

## 输出文件说明

| 文件名 | 用途 | 格式 |
|--------|------|------|
| test_results.csv | 测试结果表格 | CSV（Excel可打开） |
| test_details.txt | 详细执行日志 | 纯文本 |
| test_summary.json | 统计汇总 | JSON |

## 错误分析示例

当某个问题判断错误时，在 `test_details.txt` 中会看到：

```
!!! 错误原因分析 !!!
期望工具: SceneClassification
实际工具: ImageCaptioning
Intermediate steps数量: 2
  Step 0: AgentAction(tool='Get Photo Description', ...)
  Step 1: AgentAction(tool='Scene Classification', ...)
```

这说明模型先调用了错误的工具，我们取第一个工具作为判断依据。

## 注意事项

1. 测试过程较长，建议使用 `nohup` 或 `screen` 在后台运行
2. 测试过程中会生成大量临时图片文件在 `image/` 目录
3. 每次测试会覆盖之前的结果文件

## 统计功能

### 分类统计
测试完成后会自动统计每个工具类别的正确率：

```
每个工具类别的正确率:
====================================================================================================
工具名称                                 总数       正确       错误        正确率
----------------------------------------------------------------------------------------------------
ChangeDetection                      20       20        0    100.00%
EdgeDetection                        20       18        2     90.00%
ImageCaptioning                      20       18        2     90.00%
ObjectCounting                       20       17        3     85.00%
ObjectDetection                      20       16        4     80.00%
SceneClassification                  20       19        1     95.00%
----------------------------------------------------------------------------------------------------
总计                                  120      108       12     90.00%
====================================================================================================
```

### 独立分析脚本
也可以使用独立的分析脚本：

```bash
python analyze_results.py
```

这会读取 `test_results.csv` 并生成分类统计报告。

### JSON格式统计
`test_summary.json` 包含结构化的统计数据：

```json
{
  "overall": {
    "total": 120,
    "correct": 108,
    "incorrect": 12,
    "accuracy": "90.00%"
  },
  "by_tool": {
    "ChangeDetection": {
      "total": 20,
      "correct": 20,
      "incorrect": 0,
      "accuracy": "100.00%"
    },
    ...
  }
}
```

便于后续的数据分析和可视化。

## 日志输出说明

### 终端输出
测试运行时，终端会显示完整的执行过程：
- Agent的推理过程（Thought, Action, Observation）
- 工具的实际执行结果（如 "Change detection completed..."）
- 每个问题的测试结果和当前正确率

### test_details.txt
详细日志文件记录：
- 每个问题的基本信息（ID、内容、Ground Truth）
- 工具调用的关键信息
- 错误原因分析（如果判断错误）
- 最终统计汇总

**注意**：由于技术限制，test_details.txt 中不包含完整的Agent执行过程和工具输出。
要查看完整的执行细节，请查看终端输出或使用 `nohup` 重定向到文件：

```bash
nohup python test_rschatgpt.py > test_full_log.txt 2>&1 &
```

这样可以将所有输出（包括工具执行结果）保存到 `test_full_log.txt` 文件中。

## 图片文件管理

### 文件命名规则

测试过程中生成的图片文件使用有意义的命名：

**输入图片**：
```
q{问题ID}_{工具类型}.png
```
示例：
- `q001_ChangeDetection.png` - 问题1的输入图片（变化检测）
- `q015_EdgeDetection.png` - 问题15的输入图片（边缘检测）
- `q120_ImageCaptioning.png` - 问题120的输入图片（图像描述）

**结果图片**（由工具自动生成）：
```
{随机前缀}_{工具类型}_q{问题ID}.png
```
示例：
- `d3a8_edge_q122.png` - 问题122的边缘检测结果
- `119d_change_detection_q121.png` - 问题121的变化检测结果
- `6277_detection_airplanes_q005.png` - 问题5的目标检测结果

### 清理旧文件

提供了清理脚本 `clean_old_images.py` 来删除旧的随机命名文件：

```bash
# 预览模式（不实际删除，只显示要删除的文件）
python clean_old_images.py

# 删除模式（实际删除文件）
python clean_old_images.py --delete
```

脚本会自动识别并保留新格式的文件（`q{ID}_{ToolType}*.png`），删除旧的随机命名文件。

### 命名优势

1. **可追溯性**：通过文件名直接知道问题ID和工具类型
2. **易于管理**：按问题ID排序，方便查找特定问题的结果
3. **避免冲突**：每个问题有唯一的输入文件名
4. **便于分析**：可以快速定位和比较不同问题的输入输出
