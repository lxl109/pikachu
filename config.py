"""皮卡丘番茄钟 - 配置文件"""

# 皮卡丘配色方案
COLORS = {
    # 主色调
    "yellow": "#FBE74E",           # 皮卡丘黄 (主背景)
    "dark_yellow": "#E5C800",      # 深黄 (强调)
    "light_yellow": "#FFF9E6",     # 浅黄 (页面背景)

    # 特征色
    "red": "#FF5C5C",              # 红脸颊
    "dark_red": "#E84040",         # 深红 (悬停)
    "brown": "#6B3A1A",            # 棕色 (耳朵尖/尾巴)
    "black": "#2D2D2D",            # 黑色 (眼睛/文字)
    "white": "#FFFFFF",            # 白色

    # 辅助色
    "gray": "#8B8680",             # 灰色 (次要文字)
    "light_gray": "#F0EDE8",       # 浅灰 (边框/分隔)
    "green": "#4CAF50",            # 绿色 (成功)
    "orange": "#FF9800",           # 橙色 (警告)
}

# 默认设置
DEFAULT_SETTINGS = {
    "work_minutes": 25,
    "short_break_minutes": 5,
    "long_break_minutes": 15,
    "long_break_interval": 4,      # 几个番茄后长休息
    "sound_enabled": True,
    "notification_enabled": True,
    "auto_start_break": False,
    "auto_start_work": False,
}

# 窗口尺寸
WINDOW_WIDTH = 460
WINDOW_HEIGHT = 700

# 字体
FONTS = {
    "title": ("Microsoft YaHei", 22, "bold"),
    "subtitle": ("Microsoft YaHei", 14, "bold"),
    "timer": ("Microsoft YaHei", 56, "bold"),
    "body": ("Microsoft YaHei", 13),
    "small": ("Microsoft YaHei", 11),
    "button": ("Microsoft YaHei", 14, "bold"),
}
