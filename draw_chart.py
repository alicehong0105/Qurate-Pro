import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as patches

# 1. 建立波動數據（模擬長週期模態的弦波）
t = np.linspace(0, 11, 500)
y = 1.5 * np.sin(1.1 * t - 0.3) + 2.5

# 2. 初始化圖表
fig, ax = plt.subplots(figsize=(10, 5), dpi=300)
fig.patch.set_facecolor("#ffffff")  # 可依需求調整背景色
ax.set_facecolor("#ffffff")

# 3. 繪製主波動曲線與取樣點
ax.plot(t, y, color="#1f4e79", linewidth=2.5, zorder=2)

# 模擬原圖中的離散取樣點 (dots)
t_dots = np.linspace(0.8, 10.2, 30)
y_dots = 1.5 * np.sin(1.1 * t_dots - 0.3) + 2.5
ax.scatter(t_dots, y_dots, color="#1f4e79", s=20, zorder=3)

# 4. 繪製起始點的「小方塊」
ax.scatter([0], [y[0]], color="#1f4e79", marker="s", s=60, zorder=4)

# 5. 定義波峰與波谷的位置 (用於繪製箭頭)
# 透過數學計算找出波峰與波谷的 t 值
peak1_t = (np.pi / 2 + 0.3) / 1.1
peak2_t = (5 * np.pi / 2 + 0.3) / 1.1
trough1_t = (3 * np.pi / 2 + 0.3) / 1.1

peak1_y = 1.5 * np.sin(1.1 * peak1_t - 0.3) + 2.5
peak2_y = 1.5 * np.sin(1.1 * peak2_t - 0.3) + 2.5
trough1_y = 1.5 * np.sin(1.1 * trough1_t - 0.3) + 2.5

# 6. 繪製各式指示箭頭 (無文字)
# 軸線與波峰波谷間的垂直虛線與箭頭
ax.annotate(
    "",
    xy=(peak1_t, peak1_y),
    xytext=(peak1_t, 1.0),
    arrowprops=dict(arrowstyle="->", color="#1f4e79", linestyle="dashed", lw=1.2),
)
ax.annotate(
    "",
    xy=(trough1_t, trough1_y),
    xytext=(trough1_t, 1.0),
    arrowprops=dict(arrowstyle="->", color="#1f4e79", linestyle="dashed", lw=1.2),
)
ax.annotate(
    "",
    xy=(peak2_t, peak2_y),
    xytext=(peak2_t, 1.0),
    arrowprops=dict(arrowstyle="->", color="#1f4e79", linestyle="dashed", lw=1.2),
)

# 頂部週期 T 的雙向箭頭
ax.annotate(
    "",
    xy=(peak1_t, peak1_y + 0.4),
    xytext=(peak2_t, peak2_y + 0.4),
    arrowprops=dict(arrowstyle="<->", color="#1f4e79", lw=1.2),
)

# 7. 設定與重塑座標軸 (加上箭頭尾端樣式)
ax.spines["left"].set_position("zero")
ax.spines["bottom"].set_position(("data", 1.0))  # 將 X 軸定在下方
ax.spines["right"].set_color("none")
ax.spines["top"].set_color("none")

# 加上座標軸箭頭
ax.plot(0, 4.5, "^", color="#1f4e79", clip_on=False)  # Y軸箭頭
ax.plot(11.3, 1.0, ">", color="#1f4e79", clip_on=False)  # X軸箭頭
ax.set_xlim(-0.5, 11.3)
ax.set_ylim(0.2, 4.5)

# 8. 徹底移除所有刻度與文字
ax.set_xticks([])
ax.set_yticks([])
ax.set_xticklabels([])
ax.set_yticklabels([])

# 顯示與儲存圖表
plt.tight_layout()
plt.savefig("clean_wave_chart.png", bbox_inches="tight", dpi=300)
plt.show()
