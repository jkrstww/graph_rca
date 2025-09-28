import json
import matplotlib.pyplot as plt
import matplotlib
matplotlib.use('TkAgg')  # 或 'TkAgg'
# 设置中文字体支持
plt.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei', 'DejaVu Sans']  # 用来正常显示中文标签
plt.rcParams['axes.unicode_minus'] = False  # 用来正常显示负号

from utils.file_utils import get_encoding

def show_length(file_path):
    with open(file_path, 'r', encoding=get_encoding(file_path)) as f:
        data = json.load(f)
    f.close()

    ret = {}
    for item in data:
        list = item['path'].split('->')
        length = len(list)

        if str(length) not in ret:
            ret[str(length)] = 1
        else:
            ret[str(length)] = ret[str(length)] + 1

    with open('./graph/path_stats.json', 'w', encoding='utf-8') as f:
        json.dump(ret, f, ensure_ascii=False, indent=4)

    return ret

def show_path_stats(file_path):
    with open(file_path, 'r', encoding=get_encoding(file_path)) as f:
        data = json.load(f)
    f.close()

    keys = list(data.keys())
    values = list(data.values())

    # 创建更美观的配色方案
    colors = ['#FF6B6B', '#4ECDC4', '#45B7D1', '#FFBE0B', '#FB5607', '#8338EC']

    # 创建图表和子图
    fig, ax = plt.subplots(figsize=(10, 7))

    # 创建柱状图
    bars = ax.bar(keys, values,
                  color=colors[:len(keys)],
                  edgecolor='white',
                  linewidth=2,
                  alpha=0.8)

    # 设置图表标题和坐标轴标签
    ax.set_title('推理路径长度分析', fontsize=18, fontweight='bold', pad=20)
    ax.set_xlabel('路径长度', fontsize=14, fontweight='bold')
    ax.set_ylabel('数量', fontsize=14, fontweight='bold')

    # 在每个柱子上方添加数值标签
    for i, (bar, value) in enumerate(zip(bars, values)):
        height = bar.get_height()
        ax.text(bar.get_x() + bar.get_width() / 2, height + 0.5,
                str(value), ha='center', va='bottom',
                fontsize=14, fontweight='bold')

    # 设置网格线
    ax.grid(axis='y', alpha=0.3, linestyle='--')

    # 调整y轴范围以更好地显示数据
    ax.set_ylim(0, max(values) * 1.15)

    # 美化图表 - 移除上边框和右边框
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.spines['left'].set_alpha(0.3)
    ax.spines['bottom'].set_alpha(0.3)

    # 设置刻度标签的字体大小
    ax.tick_params(axis='both', which='major', labelsize=12)

    # 添加轻微的阴影效果
    for bar in bars:
        bar.set_edgecolor('white')
        bar.set_linewidth(2)

    # 添加水平线标记主要数值
    ax.axhline(y=34, color='gray', linestyle='--', alpha=0.3)

    # 显示图表
    plt.tight_layout()
    plt.show()

if __name__ == '__main__':
    show_path_stats('./graph/path_stats.json')