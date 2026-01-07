#!/bin/bash
# MMchange.py 一键验证脚本
# 
# 该脚本会依次运行所有验证测试，并生成测试报告
#
# 使用方法:
#   bash run_mmchange_verification.sh [cuda:0|cpu]

set -e  # 遇到错误立即退出

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 获取设备参数，默认为 cuda:0
DEVICE=${1:-cuda:0}

echo -e "${BLUE}╔════════════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║           MMchange.py 自动验证脚本                              ║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════════════════════════════╝${NC}"
echo ""
echo -e "${YELLOW}设备: ${DEVICE}${NC}"
echo ""

# 激活 conda 环境
if [ -f "/root/miniconda3/bin/activate" ]; then
    source /root/miniconda3/bin/activate mmchange
    echo -e "${GREEN}✓ 已激活 mmchange 环境${NC}"
else
    echo -e "${YELLOW}⚠ 未找到 conda，尝试使用当前环境${NC}"
fi
echo ""

# 切换到项目目录
cd /root/Remote-Sensing-ChatGPT

# 创建结果目录
RESULT_DIR="verification_results_$(date +%Y%m%d_%H%M%S)"
mkdir -p "$RESULT_DIR"

echo -e "${BLUE}═══════════════════════════════════════════════════════════════${NC}"
echo -e "${BLUE}测试 1: 直接运行验证${NC}"
echo -e "${BLUE}═══════════════════════════════════════════════════════════════${NC}"
echo ""

# 运行直接运行验证
if python test_mmchange_direct.py --device "$DEVICE" 2>&1 | tee "$RESULT_DIR/test_direct.log"; then
    echo -e "${GREEN}✓ 直接运行验证: 通过${NC}" | tee -a "$RESULT_DIR/summary.txt"
    DIRECT_TEST_PASSED=1
else
    echo -e "${RED}✗ 直接运行验证: 失败${NC}" | tee -a "$RESULT_DIR/summary.txt"
    DIRECT_TEST_PASSED=0
fi

echo ""
echo -e "${BLUE}═══════════════════════════════════════════════════════════════${NC}"
echo -e "${BLUE}测试 2: Tool 调用验证${NC}"
echo -e "${BLUE}═══════════════════════════════════════════════════════════════${NC}"
echo ""

# 运行 Tool 调用验证
if python test_mmchange_as_tool.py --device "$DEVICE" 2>&1 | tee "$RESULT_DIR/test_as_tool.log"; then
    echo -e "${GREEN}✓ Tool 调用验证: 通过${NC}" | tee -a "$RESULT_DIR/summary.txt"
    TOOL_TEST_PASSED=1
else
    echo -e "${RED}✗ Tool 调用验证: 失败${NC}" | tee -a "$RESULT_DIR/summary.txt"
    TOOL_TEST_PASSED=0
fi

# 生成总结报告
echo ""
echo -e "${BLUE}═══════════════════════════════════════════════════════════════${NC}"
echo -e "${BLUE}验证结果总结${NC}"
echo -e "${BLUE}═══════════════════════════════════════════════════════════════${NC}"
echo ""

echo "MMchange.py 验证报告" | tee "$RESULT_DIR/report.txt"
echo "===================" | tee -a "$RESULT_DIR/report.txt"
echo "" | tee -a "$RESULT_DIR/report.txt"
echo "测试时间: $(date)" | tee -a "$RESULT_DIR/report.txt"
echo "测试设备: $DEVICE" | tee -a "$RESULT_DIR/report.txt"
echo "" | tee -a "$RESULT_DIR/report.txt"
echo "测试结果:" | tee -a "$RESULT_DIR/report.txt"
echo "---------" | tee -a "$RESULT_DIR/report.txt"

if [ $DIRECT_TEST_PASSED -eq 1 ]; then
    echo -e "  ${GREEN}✓ 直接运行验证: 通过${NC}" | tee -a "$RESULT_DIR/report.txt"
else
    echo -e "  ${RED}✗ 直接运行验证: 失败${NC}" | tee -a "$RESULT_DIR/report.txt"
fi

if [ $TOOL_TEST_PASSED -eq 1 ]; then
    echo -e "  ${GREEN}✓ Tool 调用验证: 通过${NC}" | tee -a "$RESULT_DIR/report.txt"
else
    echo -e "  ${RED}✗ Tool 调用验证: 失败${NC}" | tee -a "$RESULT_DIR/report.txt"
fi

echo "" | tee -a "$RESULT_DIR/report.txt"

# 检查测试结果
if [ $DIRECT_TEST_PASSED -eq 1 ] && [ $TOOL_TEST_PASSED -eq 1 ]; then
    echo -e "${GREEN}╔════════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${GREEN}║  🎉 所有验证通过！MMchange.py 可以正常使用                      ║${NC}"
    echo -e "${GREEN}╚════════════════════════════════════════════════════════════════╝${NC}"
    echo "" | tee -a "$RESULT_DIR/report.txt"
    echo "结论: ✓ 所有验证通过" | tee -a "$RESULT_DIR/report.txt"
    EXIT_CODE=0
else
    echo -e "${RED}╔════════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${RED}║  ❌ 部分验证失败，请检查日志文件                                ║${NC}"
    echo -e "${RED}╚════════════════════════════════════════════════════════════════╝${NC}"
    echo "" | tee -a "$RESULT_DIR/report.txt"
    echo "结论: ✗ 部分验证失败" | tee -a "$RESULT_DIR/report.txt"
    EXIT_CODE=1
fi

echo ""
echo -e "${BLUE}详细日志和结果保存在: $RESULT_DIR/${NC}"
echo ""
echo "文件列表:"
ls -lh "$RESULT_DIR"

# 如果有测试结果图像，也列出来
if [ -d "test_results" ]; then
    echo ""
    echo "生成的结果图像:"
    ls -lh test_results/*.png 2>/dev/null || echo "  (无)"
fi

if [ -d "image" ]; then
    echo ""
    echo "Tool 调用生成的图像:"
    ls -lh image/*change*.png 2>/dev/null || echo "  (无)"
fi

echo ""
echo -e "${YELLOW}查看完整报告: cat $RESULT_DIR/report.txt${NC}"
echo -e "${YELLOW}查看直接运行日志: cat $RESULT_DIR/test_direct.log${NC}"
echo -e "${YELLOW}查看 Tool 调用日志: cat $RESULT_DIR/test_as_tool.log${NC}"
echo ""

exit $EXIT_CODE

