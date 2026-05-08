"""皮卡丘番茄钟 - 主程序"""

import json
import os
import sys
import threading
import time
import tkinter as tk
import winsound
from datetime import datetime, timedelta

import customtkinter as ctk
import pystray
from PIL import Image, ImageDraw, ImageTk
from plyer import notification

from config import COLORS, DEFAULT_SETTINGS, FONTS, WINDOW_HEIGHT, WINDOW_WIDTH

# 数据文件路径
DATA_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data.json")


def create_pikachu_icon(size=64):
    """生成皮卡丘风格图标"""
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    r = size // 2
    ear_h = size // 3

    # 左耳 (黄)
    draw.polygon(
        [(r - size // 3, size // 4), (r - size // 2, 0), (r - size // 6, size // 8)],
        fill=COLORS["yellow"],
    )
    # 左耳尖 (棕)
    draw.polygon(
        [(r - size // 2, 0), (r - size // 2 + 4, 6), (r - size // 2 - 2, 8)],
        fill=COLORS["brown"],
    )
    # 右耳 (黄)
    draw.polygon(
        [(r + size // 3, size // 4), (r + size // 2, 0), (r + size // 6, size // 8)],
        fill=COLORS["yellow"],
    )
    # 右耳尖 (棕)
    draw.polygon(
        [(r + size // 2, 0), (r + size // 2 - 4, 6), (r + size // 2 + 2, 8)],
        fill=COLORS["brown"],
    )

    # 黄圆 (脸)
    face_r = size // 2 - 4
    draw.ellipse(
        [(r - face_r, r - face_r + 4), (r + face_r, r + face_r + 4)],
        fill=COLORS["yellow"],
    )

    # 黑眼睛
    eye_r = size // 12
    draw.ellipse(
        [(r - size // 4 - eye_r, r - eye_r - 2), (r - size // 4 + eye_r, r - eye_r + 2 * eye_r - 2)],
        fill=COLORS["black"],
    )
    draw.ellipse(
        [(r + size // 4 - eye_r, r - eye_r - 2), (r + size // 4 + eye_r, r - eye_r + 2 * eye_r - 2)],
        fill=COLORS["black"],
    )
    # 白高光
    hl_r = eye_r // 2
    draw.ellipse(
        [(r - size // 4 - hl_r - 1, r - 2 * hl_r), (r - size // 4 + hl_r - 1, r)],
        fill=COLORS["white"],
    )
    draw.ellipse(
        [(r + size // 4 - hl_r - 1, r - 2 * hl_r), (r + size // 4 + hl_r - 1, r)],
        fill=COLORS["white"],
    )

    # 红脸颊
    cheek_r = size // 8
    draw.ellipse(
        [(r - size // 2, r + 4), (r - size // 2 + 2 * cheek_r, r + 4 + 2 * cheek_r)],
        fill=COLORS["red"],
    )
    draw.ellipse(
        [(r + size // 2 - 2 * cheek_r, r + 4), (r + size // 2, r + 4 + 2 * cheek_r)],
        fill=COLORS["red"],
    )

    # 鼻子
    draw.ellipse([(r - 2, r + 2), (r + 2, r + 6)], fill=COLORS["black"])

    # 嘴巴
    draw.arc([(r - 10, r + 4), (r + 10, r + 16)], start=0, end=180, fill=COLORS["black"], width=2)

    return img


class CircularProgress(tk.Canvas):
    """圆形进度条"""

    def __init__(self, parent, size=240, bg_color=COLORS["yellow"],
                 track_color=COLORS["light_yellow"], progress_color=COLORS["red"],
                 **kwargs):
        super().__init__(parent, width=size, height=size,
                         bg=bg_color, highlightthickness=0, **kwargs)
        self.size = size
        self.center = size // 2
        self.radius = (size - 24) // 2
        self.track_color = track_color
        self.progress_color = progress_color
        self._draw()

    def _draw(self):
        self.delete("all")
        # 背景圆环
        self.create_oval(
            self.center - self.radius, self.center - self.radius,
            self.center + self.radius, self.center + self.radius,
            outline=self.track_color, width=8,
        )
        # 进度弧 (初始为0)
        self.arc_id = self.create_arc(
            self.center - self.radius, self.center - self.radius,
            self.center + self.radius, self.center + self.radius,
            start=90, extent=0,
            outline=self.progress_color, width=8, style="arc",
        )

    def set_progress(self, value):
        """设置进度 0.0 - 1.0"""
        extent = -360 * value
        self.itemconfig(self.arc_id, extent=extent)


class TimerEngine:
    """计时器引擎"""

    def __init__(self, settings):
        self.settings = settings
        self.work_minutes = settings["work_minutes"]
        self.short_break = settings["short_break_minutes"]
        self.long_break = settings["long_break_minutes"]
        self.long_break_interval = settings["long_break_interval"]
        self.is_working = True
        self.is_running = False
        self.seconds_left = self.work_minutes * 60
        self.completed_pomodoros = 0
        self.current_task = ""

    def start(self):
        self.is_running = True

    def pause(self):
        self.is_running = False

    def reset(self):
        self.is_running = False
        self.seconds_left = self.work_minutes * 60 if self.is_working else self.short_break * 60

    def skip(self):
        self.is_running = False
        self._complete_phase()

    def tick(self):
        if self.is_running and self.seconds_left > 0:
            self.seconds_left -= 1
            return True
        return False

    def is_complete(self):
        return self.seconds_left <= 0

    def _complete_phase(self):
        if self.is_working:
            self.completed_pomodoros += 1
        self.is_working = not self.is_working
        self.is_running = False

        if self.is_working:
            self.seconds_left = self.work_minutes * 60
        else:
            if self.completed_pomodoros > 0 and self.completed_pomodoros % self.long_break_interval == 0:
                self.seconds_left = self.long_break * 60
            else:
                self.seconds_left = self.short_break * 60

    def complete(self):
        self._complete_phase()

    def get_total_seconds(self):
        if self.is_working:
            return self.work_minutes * 60
        else:
            if self.completed_pomodoros > 0 and self.completed_pomodoros % self.long_break_interval == 0:
                return self.long_break * 60
            return self.short_break * 60

    def get_progress(self):
        total = self.get_total_seconds()
        if total == 0:
            return 0
        return 1 - (self.seconds_left / total)


class DataManager:
    """数据管理"""

    def __init__(self, filepath):
        self.filepath = filepath
        self.data = self._load()

    def _load(self):
        if os.path.exists(self.filepath):
            try:
                with open(self.filepath, "r", encoding="utf-8") as f:
                    return json.load(f)
            except (json.JSONDecodeError, IOError):
                pass
        return {
            "settings": DEFAULT_SETTINGS.copy(),
            "history": [],
        }

    def save(self):
        with open(self.filepath, "w", encoding="utf-8") as f:
            json.dump(self.data, f, ensure_ascii=False, indent=2)

    def get_settings(self):
        return self.data.get("settings", DEFAULT_SETTINGS.copy())

    def update_settings(self, settings):
        self.data["settings"] = settings
        self.save()

    def add_pomodoro(self, task_name, duration_minutes):
        entry = {
            "task": task_name,
            "duration": duration_minutes,
            "date": datetime.now().strftime("%Y-%m-%d"),
            "time": datetime.now().strftime("%H:%M"),
        }
        self.data.setdefault("history", []).insert(0, entry)
        # 只保留最近100条
        self.data["history"] = self.data["history"][:100]
        self.save()

    def get_history(self, days=7):
        """获取最近几天的历史"""
        cutoff = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")
        return [h for h in self.data.get("history", []) if h.get("date", "") >= cutoff]

    def get_today_count(self):
        today = datetime.now().strftime("%Y-%m-%d")
        return sum(1 for h in self.data.get("history", []) if h.get("date") == today)


class PomodoroApp:
    """主应用"""

    def __init__(self):
        self.data_mgr = DataManager(DATA_FILE)
        self.settings = self.data_mgr.get_settings()
        self.timer = TimerEngine(self.settings)
        self.tray_icon = None
        self.tray_thread = None

        # 初始化 customtkinter
        ctk.set_appearance_mode("light")
        ctk.set_default_color_theme("blue")

        # 创建主窗口
        self.root = ctk.CTk()
        self.root.title("皮卡丘番茄钟")
        self.root.geometry(f"{WINDOW_WIDTH}x{WINDOW_HEIGHT}")
        self.root.minsize(400, 600)
        self.root.configure(fg_color=COLORS["light_yellow"])

        # 窗口图标
        try:
            icon_img = create_pikachu_icon(32)
            self._icon_photo = ImageTk.PhotoImage(icon_img)
            self.root.iconphoto(False, self._icon_photo)
        except Exception:
            pass

        # 关闭处理
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)

        self._create_ui()
        self._update_display()
        self._refresh_history()

        # 计时线程
        self._stop_thread = False
        self._timer_thread = threading.Thread(target=self._timer_loop, daemon=True)
        self._timer_thread.start()

    def _create_ui(self):
        """创建用户界面"""
        # 主容器
        main = ctk.CTkFrame(self.root, fg_color=COLORS["light_yellow"], corner_radius=0)
        main.pack(fill="both", expand=True, padx=16, pady=12)

        # ===== 顶部工具栏 =====
        top = ctk.CTkFrame(main, fg_color="transparent")
        top.pack(fill="x", pady=(0, 8))

        # 皮卡丘标题
        title_frame = ctk.CTkFrame(top, fg_color="transparent")
        title_frame.pack(side="left")

        icon_label = ctk.CTkLabel(
            title_frame, text="⚡",
            font=("Microsoft YaHei", 24),
            text_color=COLORS["dark_yellow"],
        )
        icon_label.pack(side="left")

        ctk.CTkLabel(
            title_frame, text="皮卡丘番茄钟",
            font=FONTS["title"],
            text_color=COLORS["black"],
        ).pack(side="left", padx=(4, 0))

        # 工具按钮
        btn_frame = ctk.CTkFrame(top, fg_color="transparent")
        btn_frame.pack(side="right")

        self.topmost_btn = ctk.CTkButton(
            btn_frame, text="📌", width=36, height=36,
            font=("Microsoft YaHei", 14),
            fg_color=COLORS["light_gray"], hover_color=COLORS["gray"],
            text_color=COLORS["black"],
            corner_radius=10,
            command=self._toggle_topmost,
        )
        self.topmost_btn.pack(side="left", padx=2)

        self.tray_btn = ctk.CTkButton(
            btn_frame, text="🗕", width=36, height=36,
            font=("Microsoft YaHei", 14),
            fg_color=COLORS["light_gray"], hover_color=COLORS["gray"],
            text_color=COLORS["black"],
            corner_radius=10,
            command=self._minimize_to_tray,
        )
        self.tray_btn.pack(side="left", padx=2)

        # ===== 模式标签 =====
        self.mode_label = ctk.CTkLabel(
            main, text="⚡ 专注工作 ⚡",
            font=FONTS["subtitle"],
            text_color=COLORS["dark_yellow"],
        )
        self.mode_label.pack(pady=(4, 0))

        self.mode_desc = ctk.CTkLabel(
            main, text="保持专注,完成一个番茄钟!",
            font=FONTS["small"],
            text_color=COLORS["gray"],
        )
        self.mode_desc.pack(pady=(0, 8))

        # ===== 圆形进度 + 时间显示 =====
        timer_container = ctk.CTkFrame(
            main, fg_color=COLORS["yellow"],
            corner_radius=24, border_width=0,
        )
        timer_container.pack(pady=8, padx=20)

        self.progress = CircularProgress(
            timer_container, size=220,
            bg_color=COLORS["yellow"],
            track_color=COLORS["light_yellow"],
            progress_color=COLORS["red"],
        )
        self.progress.pack(padx=20, pady=(20, 0))

        self.timer_label = ctk.CTkLabel(
            timer_container, text="25:00",
            font=FONTS["timer"],
            text_color=COLORS["black"],
        )
        self.timer_label.place(in_=self.progress, x=110, y=110, anchor="center")

        # 当前任务标签
        self.current_task_label = ctk.CTkLabel(
            timer_container, text="当前任务: 未设置",
            font=FONTS["small"],
            text_color=COLORS["brown"],
        )
        self.current_task_label.pack(pady=(0, 16))

        # ===== 控制按钮 =====
        ctrl_frame = ctk.CTkFrame(main, fg_color="transparent")
        ctrl_frame.pack(pady=12)

        self.start_btn = ctk.CTkButton(
            ctrl_frame, text="▶ 开始", width=120, height=44,
            font=FONTS["button"],
            fg_color=COLORS["green"], hover_color="#45a049",
            text_color=COLORS["white"],
            corner_radius=12,
            command=self._on_start,
        )
        self.start_btn.pack(side="left", padx=6)

        self.reset_btn = ctk.CTkButton(
            ctrl_frame, text="↺ 重置", width=90, height=44,
            font=FONTS["body"],
            fg_color=COLORS["gray"], hover_color="#6B6560",
            text_color=COLORS["white"],
            corner_radius=12,
            command=self._on_reset,
        )
        self.reset_btn.pack(side="left", padx=6)

        self.skip_btn = ctk.CTkButton(
            ctrl_frame, text="⏭ 跳过", width=90, height=44,
            font=FONTS["body"],
            fg_color=COLORS["orange"], hover_color="#E68900",
            text_color=COLORS["white"],
            corner_radius=12,
            command=self._on_skip,
        )
        self.skip_btn.pack(side="left", padx=6)

        # ===== 任务输入 =====
        task_frame = ctk.CTkFrame(
            main, fg_color=COLORS["white"],
            corner_radius=12, border_width=1,
            border_color=COLORS["light_gray"],
        )
        task_frame.pack(fill="x", pady=12)

        task_inner = ctk.CTkFrame(task_frame, fg_color="transparent")
        task_inner.pack(fill="x", padx=12, pady=10)

        self.task_entry = ctk.CTkEntry(
            task_inner,
            placeholder_text="输入当前任务名称...",
            font=FONTS["body"],
            fg_color=COLORS["light_yellow"],
            border_color=COLORS["yellow"],
            text_color=COLORS["black"],
            corner_radius=8,
            height=36,
        )
        self.task_entry.pack(side="left", fill="x", expand=True, padx=(0, 8))
        self.task_entry.bind("<Return>", lambda e: self._set_task())

        task_set_btn = ctk.CTkButton(
            task_inner, text="设置", width=60, height=36,
            font=FONTS["small"],
            fg_color=COLORS["yellow"], hover_color=COLORS["dark_yellow"],
            text_color=COLORS["black"],
            corner_radius=8,
            command=self._set_task,
        )
        task_set_btn.pack(side="right")

        # ===== 今日统计 =====
        self.stats_label = ctk.CTkLabel(
            main, text="今日完成: 0 个番茄 🍅",
            font=FONTS["body"],
            text_color=COLORS["black"],
        )
        self.stats_label.pack(pady=4)

        # ===== 历史记录 =====
        history_container = ctk.CTkFrame(
            main, fg_color=COLORS["white"],
            corner_radius=12, border_width=1,
            border_color=COLORS["light_gray"],
        )
        history_container.pack(fill="both", expand=True, pady=8)

        history_header = ctk.CTkFrame(history_container, fg_color="transparent")
        history_header.pack(fill="x", padx=12, pady=(8, 4))

        ctk.CTkLabel(
            history_header, text="📋 近期记录",
            font=FONTS["subtitle"],
            text_color=COLORS["black"],
        ).pack(side="left")

        self.settings_btn = ctk.CTkButton(
            history_header, text="⚙ 设置", width=70, height=28,
            font=FONTS["small"],
            fg_color=COLORS["light_gray"], hover_color=COLORS["gray"],
            text_color=COLORS["black"],
            corner_radius=8,
            command=self._show_settings,
        )
        self.settings_btn.pack(side="right")

        # 历史列表 (ScrollableFrame)
        self.history_frame = ctk.CTkScrollableFrame(
            history_container,
            fg_color="transparent",
            scrollbar_button_color=COLORS["yellow"],
            scrollbar_button_hover_color=COLORS["dark_yellow"],
        )
        self.history_frame.pack(fill="both", expand=True, padx=8, pady=4)

    def _timer_loop(self):
        """计时器后台线程"""
        while not self._stop_thread:
            if self.timer.is_running:
                self.timer.tick()
                self.root.after(0, self._update_display)
                if self.timer.is_complete():
                    self.root.after(0, self._on_timer_complete)
            time.sleep(1)

    def _update_display(self):
        """更新显示"""
        minutes = self.timer.seconds_left // 60
        seconds = self.timer.seconds_left % 60
        time_str = f"{minutes:02d}:{seconds:02d}"
        self.timer_label.configure(text=time_str)
        self.progress.set_progress(self.timer.get_progress())

        # 更新窗口标题
        mode = "专注" if self.timer.is_working else "休息"
        status = "▶" if self.timer.is_running else "⏸"
        self.root.title(f"{status} {time_str} - {mode} | 皮卡丘番茄钟")

        # 更新模式标签
        if self.timer.is_working:
            self.mode_label.configure(text="⚡ 专注工作 ⚡", text_color=COLORS["dark_yellow"])
            self.mode_desc.configure(text="保持专注,完成一个番茄钟!")
        else:
            self.mode_label.configure(text="☕ 休息时刻 ☕", text_color=COLORS["green"])
            self.mode_desc.configure(text="放松一下,充充电吧~")

    def _on_start(self):
        """开始/暂停按钮"""
        if self.timer.is_running:
            self.timer.pause()
            self.start_btn.configure(
                text="▶ 开始",
                fg_color=COLORS["green"], hover_color="#45a049",
            )
        else:
            self.timer.start()
            self.start_btn.configure(
                text="⏸ 暂停",
                fg_color=COLORS["red"], hover_color=COLORS["dark_red"],
            )

    def _on_reset(self):
        """重置按钮"""
        self.timer.reset()
        self.start_btn.configure(
            text="▶ 开始",
            fg_color=COLORS["green"], hover_color="#45a049",
        )
        self._update_display()

    def _on_skip(self):
        """跳过当前阶段"""
        self.timer.skip()
        self.start_btn.configure(
            text="▶ 开始",
            fg_color=COLORS["green"], hover_color="#45a049",
        )
        self._update_display()

    def _on_timer_complete(self):
        """计时器完成处理"""
        self.timer.is_running = False

        if self.timer.is_working:
            # 工作完成
            duration = self.timer.work_minutes
            task = self.timer.current_task or "未命名任务"
            self.data_mgr.add_pomodoro(task, duration)
            self._refresh_history()

            if self.settings.get("notification_enabled", True):
                self._notify("番茄钟 - 工作完成!", f"🎉 「{task}」完成!\n休息一下吧~")
            if self.settings.get("sound_enabled", True):
                self._play_complete_sound()
        else:
            # 休息完成
            if self.settings.get("notification_enabled", True):
                self._notify("番茄钟 - 休息结束!", "⚡ 休息结束!\n开始新的专注吧!")
            if self.settings.get("sound_enabled", True):
                self._play_break_end_sound()

        self.timer.complete()
        self.start_btn.configure(
            text="▶ 开始",
            fg_color=COLORS["green"], hover_color="#45a049",
        )
        self._update_display()

        # 自动开始
        if self.timer.is_working and self.settings.get("auto_start_work", False):
            self._on_start()
        elif not self.timer.is_working and self.settings.get("auto_start_break", False):
            self._on_start()

    def _notify(self, title, message):
        """发送桌面通知"""
        try:
            notification.notify(
                title=title,
                message=message,
                app_name="皮卡丘番茄钟",
                timeout=5,
            )
        except Exception:
            pass

    def _play_complete_sound(self):
        """播放完成提示音"""
        try:
            winsound.MessageBeep(winsound.MB_ICONASTERISK)
        except Exception:
            pass

    def _play_break_end_sound(self):
        """播放休息结束提示音"""
        try:
            winsound.MessageBeep(winsound.MB_ICONEXCLAMATION)
        except Exception:
            pass

    def _set_task(self):
        """设置当前任务"""
        task = self.task_entry.get().strip()
        if task:
            self.timer.current_task = task
            self.current_task_label.configure(text=f"当前任务: {task}")
            self.task_entry.delete(0, "end")

    def _toggle_topmost(self):
        """切换窗口置顶"""
        is_top = self.root.attributes("-topmost")
        self.root.attributes("-topmost", not is_top)
        if not is_top:
            self.topmost_btn.configure(
                fg_color=COLORS["yellow"],
                hover_color=COLORS["dark_yellow"],
            )
        else:
            self.topmost_btn.configure(
                fg_color=COLORS["light_gray"],
                hover_color=COLORS["gray"],
            )

    def _minimize_to_tray(self):
        """最小化到系统托盘"""
        self.root.withdraw()
        self._show_tray_icon()

    def _show_tray_icon(self):
        """显示托盘图标"""
        if self.tray_icon is not None:
            return

        menu = pystray.Menu(
            pystray.MenuItem("显示窗口", self._restore_from_tray),
            pystray.MenuItem("开始/暂停", self._tray_toggle_timer),
            pystray.MenuItem("退出", self._tray_exit),
        )

        icon_img = create_pikachu_icon(64)
        self.tray_icon = pystray.Icon(
            "pomodoro_pikachu",
            icon_img,
            "皮卡丘番茄钟",
            menu,
        )
        self.tray_thread = threading.Thread(target=self.tray_icon.run, daemon=True)
        self.tray_thread.start()

    def _restore_from_tray(self, icon=None, item=None):
        """从托盘恢复窗口"""
        if self.tray_icon:
            self.tray_icon.stop()
            self.tray_icon = None
        self.root.deiconify()
        self.root.lift()
        self.root.focus_force()

    def _tray_toggle_timer(self, icon=None, item=None):
        """托盘菜单: 开始/暂停"""
        self.root.after(0, self._on_start)

    def _tray_exit(self, icon=None, item=None):
        """托盘菜单: 退出"""
        if self.tray_icon:
            self.tray_icon.stop()
            self.tray_icon = None
        self._stop_thread = True
        self.root.after(0, self.root.destroy)

    def _show_settings(self):
        """显示设置窗口"""
        settings_win = ctk.CTkToplevel(self.root)
        settings_win.title("设置")
        settings_win.geometry("360x420")
        settings_win.configure(fg_color=COLORS["light_yellow"])
        settings_win.transient(self.root)
        settings_win.grab_set()

        # 居中
        x = self.root.winfo_x() + (WINDOW_WIDTH - 360) // 2
        y = self.root.winfo_y() + (WINDOW_HEIGHT - 420) // 2
        settings_win.geometry(f"+{x}+{y}")

        container = ctk.CTkFrame(settings_win, fg_color="transparent")
        container.pack(fill="both", expand=True, padx=20, pady=20)

        ctk.CTkLabel(
            container, text="⚙ 设置",
            font=FONTS["title"],
            text_color=COLORS["black"],
        ).pack(pady=(0, 16))

        # 工作时长
        self._create_setting_row(
            container, "工作时长 (分钟)",
            self.settings.get("work_minutes", 25),
            "work_minutes",
        )

        # 休息时长
        self._create_setting_row(
            container, "休息时长 (分钟)",
            self.settings.get("short_break_minutes", 5),
            "short_break_minutes",
        )

        # 长休息时长
        self._create_setting_row(
            container, "长休息时长 (分钟)",
            self.settings.get("long_break_minutes", 15),
            "long_break_minutes",
        )

        # 声音开关
        sound_frame = ctk.CTkFrame(container, fg_color="transparent")
        sound_frame.pack(fill="x", pady=8)
        ctk.CTkLabel(
            sound_frame, text="声音提醒",
            font=FONTS["body"],
            text_color=COLORS["black"],
        ).pack(side="left")
        self.sound_switch = ctk.CTkSwitch(
            sound_frame, text="",
            onvalue=True, offvalue=False,
            fg_color=COLORS["gray"],
            progress_color=COLORS["yellow"],
            button_color=COLORS["white"],
            button_hover_color=COLORS["light_gray"],
        )
        self.sound_switch.pack(side="right")
        self.sound_switch.select() if self.settings.get("sound_enabled", True) else self.sound_switch.deselect()

        # 通知开关
        notif_frame = ctk.CTkFrame(container, fg_color="transparent")
        notif_frame.pack(fill="x", pady=8)
        ctk.CTkLabel(
            notif_frame, text="桌面通知",
            font=FONTS["body"],
            text_color=COLORS["black"],
        ).pack(side="left")
        self.notif_switch = ctk.CTkSwitch(
            notif_frame, text="",
            onvalue=True, offvalue=False,
            fg_color=COLORS["gray"],
            progress_color=COLORS["yellow"],
            button_color=COLORS["white"],
            button_hover_color=COLORS["light_gray"],
        )
        self.notif_switch.pack(side="right")
        self.notif_switch.select() if self.settings.get("notification_enabled", True) else self.notif_switch.deselect()

        # 保存按钮
        save_btn = ctk.CTkButton(
            container, text="保存设置", width=140, height=40,
            font=FONTS["button"],
            fg_color=COLORS["yellow"], hover_color=COLORS["dark_yellow"],
            text_color=COLORS["black"],
            corner_radius=12,
            command=lambda: self._save_settings(settings_win),
        )
        save_btn.pack(pady=20)

    def _create_setting_row(self, parent, label, value, key):
        """创建设置行"""
        frame = ctk.CTkFrame(parent, fg_color="transparent")
        frame.pack(fill="x", pady=6)
        ctk.CTkLabel(
            frame, text=label,
            font=FONTS["body"],
            text_color=COLORS["black"],
        ).pack(side="left")
        entry = ctk.CTkEntry(
            frame, width=60, height=32,
            font=FONTS["body"],
            fg_color=COLORS["white"],
            border_color=COLORS["yellow"],
            text_color=COLORS["black"],
            corner_radius=8,
            justify="center",
        )
        entry.insert(0, str(value))
        entry.pack(side="right")
        setattr(self, f"setting_{key}", entry)

    def _save_settings(self, win):
        """保存设置"""
        try:
            self.settings["work_minutes"] = int(self.setting_work_minutes.get())
            self.settings["short_break_minutes"] = int(self.setting_short_break_minutes.get())
            self.settings["long_break_minutes"] = int(self.setting_long_break_minutes.get())
            self.settings["sound_enabled"] = bool(self.sound_switch.get())
            self.settings["notification_enabled"] = bool(self.notif_switch.get())

            self.data_mgr.update_settings(self.settings)

            # 更新计时器设置
            self.timer.work_minutes = self.settings["work_minutes"]
            self.timer.short_break = self.settings["short_break_minutes"]
            self.timer.long_break = self.settings["long_break_minutes"]
            self.timer.reset()
            self._update_display()

            win.destroy()
        except ValueError:
            # 输入无效,静默忽略或显示提示
            pass

    def _refresh_history(self):
        """刷新历史记录列表"""
        # 清除现有条目
        for widget in self.history_frame.winfo_children():
            widget.destroy()

        history = self.data_mgr.get_history(days=7)
        today = datetime.now().strftime("%Y-%m-%d")

        if not history:
            ctk.CTkLabel(
                self.history_frame, text="暂无记录,开始你的第一个番茄吧! 🍅",
                font=FONTS["small"],
                text_color=COLORS["gray"],
            ).pack(pady=20)
            self.stats_label.configure(text="今日完成: 0 个番茄 🍅")
            return

        # 按日期分组
        grouped = {}
        for h in history:
            date = h.get("date", "未知")
            grouped.setdefault(date, []).append(h)

        total_today = self.data_mgr.get_today_count()
        self.stats_label.configure(text=f"今日完成: {total_today} 个番茄 🍅")

        for date in sorted(grouped.keys(), reverse=True):
            entries = grouped[date]
            date_label = "今天" if date == today else (
                "昨天" if date == (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d") else date
            )

            # 日期分组标题
            ctk.CTkLabel(
                self.history_frame, text=f"📅 {date_label} ({len(entries)}个)",
                font=FONTS["small"],
                text_color=COLORS["brown"],
            ).pack(anchor="w", pady=(8, 2))

            for entry in entries:
                row = ctk.CTkFrame(
                    self.history_frame,
                    fg_color=COLORS["light_yellow"],
                    corner_radius=8,
                )
                row.pack(fill="x", pady=2)

                task_name = entry.get("task", "未命名")
                task_time = entry.get("time", "")
                task_duration = entry.get("duration", 25)

                ctk.CTkLabel(
                    row, text=f"🍅 {task_name}",
                    font=FONTS["small"],
                    text_color=COLORS["black"],
                ).pack(side="left", padx=8, pady=6)

                ctk.CTkLabel(
                    row, text=f"{task_time} · {task_duration}分钟",
                    font=("Microsoft YaHei", 10),
                    text_color=COLORS["gray"],
                ).pack(side="right", padx=8, pady=6)

    def on_close(self):
        """关闭窗口"""
        self._stop_thread = True
        if self.tray_icon:
            self.tray_icon.stop()
        self.root.destroy()

    def run(self):
        """运行应用"""
        self.root.mainloop()


def main():
    app = PomodoroApp()
    app.run()


if __name__ == "__main__":
    main()
