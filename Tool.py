import threading
import subprocess
import re
import os
import matplotlib.pyplot as plt
import matplotlib.animation as animation
import time as t

# 创建子图
fig = plt.figure()
ax = fig.add_subplot(1, 1, 1)

# 创建三条曲线
mem_free_line, = ax.plot([], [], label='MemFree')
mem_available_line, = ax.plot([], [], label='MemAvailable')
swap_free_line, = ax.plot([], [], label='SwapFree')

# 设置图形界面大小
fig.set_size_inches(12, 9)

# 定义变量
mem_free_history = [0] * 100
mem_available_history = [0] * 100
swap_free_history = [0] * 100
time = list(range(0, 100))
lock = threading.Lock()


# 获取内存信息的函数
def get_memory_info():
    memory_info = subprocess.check_output("adb shell cat /proc/meminfo", shell=True)
    memory_info = memory_info.decode("utf-8")
    memory_info_dict = {}

    for line in memory_info.split('\n'):
        if not line.strip():
            continue
        key, value, unit = re.findall(r'^(\S+):\s+(\d+)(?:\s+(\S+))?', line)[0]
        if unit.lower() == 'kb':
            value = int(value) / 1024
        elif unit.lower() == 'mb':
            value = int(value)
        elif unit.lower() == 'gb':
            value = int(value) * 1024
        memory_info_dict[key] = value

    return memory_info_dict


# 保存内存信息到日志文件中的函数
def save_meminfo_to_log():
    i = 0
    while True:
        # 获取内存信息
        memory_info = get_memory_info()

        # 构建日志文件名
        log_dir = 'meminfo_logs'
        if not os.path.exists(log_dir):
            os.mkdir(log_dir)

        print('Saving meminfo to log...')
        log_file = os.path.join(log_dir, f'{i:02d}.log')
        i += 1

        # 将内存信息保存到日志文件中
        with open(log_file, 'w') as f:
            for key, value in memory_info.items():
                f.write(f'{key}: {value}\n')

        # 等待1秒
        t.sleep(1)


# 创建保存内存信息到日志文件中的线程
log_thread = threading.Thread(target=save_meminfo_to_log)
log_thread.daemon = True
log_thread.start()


# 更新曲线的函数
def update_chart(frame):
    global mem_free_history, mem_available_history, swap_free_history, time

    # 获取内存信息
    memory_info = get_memory_info()

    with lock:
        # 更新MemFree信息
        mem_free_history.insert(0, memory_info['MemFree'])
        mem_free_history.pop()
        mem_free_line.set_data(time, mem_free_history)

        # 更新MemAvailable信息
        mem_available_history.insert(0, memory_info['MemAvailable'])
        mem_available_history.pop()
        mem_available_line.set_data(time, mem_available_history)

        # 更新SwapFree信息
        swap_free_history.insert(0, memory_info['SwapFree'])
        swap_free_history.pop()
        swap_free_line.set_data(time, swap_free_history)

        # 更新x轴刻度和标签
        ax.set_xticks(list(range(0, 100, 5)))
        ax.set_xticklabels([f"{i:02d}" for i in range(0, 100, 5)])

        ax.relim()
        ax.autoscale_view()





# 设置y轴范围
ax.set_ylim(0, 2000)

# 设置标题
ax.set_title('Android Memory Information')

# 设置图例位置
ax.legend(loc='upper right')

# 开始动画
ani = animation.FuncAnimation(fig, update_chart, frames=100, interval=1000, cache_frame_data=False)

# 添加一个垂直对象
vline = ax.axvline(x=0, color='b', linestyle='--', visible=False)

# 创建一个文本框，用于显示meminfo
textbox = ax.text(0.05, 0.95, '', transform=ax.transAxes, verticalalignment='top', bbox=dict(facecolor='white', alpha=0.7))

# 更新文本框
def update_textbox(x):
    log_dir = 'meminfo_logs'
    log_file = os.path.join(log_dir, f'{x:02d}.log')
    if not os.path.exists(log_file):
        return 'No meminfo available'

    with open(log_file, 'r') as f:
        content = f.read()
        return content

# 鼠标事件
def on_mouse_move(event):
    global vline, textbox

    if not event.inaxes:
        return

    # 更新纵线位置
    vline.set_xdata(event.xdata)
    vline.set_visible(True)

    # 更新文本框的内容
    x = int(event.xdata)
    textbox.set_text(update_textbox(x))

    # 重绘图形
    fig.canvas.draw_idle()

# 绑定鼠标移动事件
fig.canvas.mpl_connect('motion_notify_event', on_mouse_move)

# 显示图形界面
plt.show()


