import os
import sys
import json
import time
import random
import ctypes
import tkinter as tk
from tkinter import filedialog, messagebox
from datetime import datetime, timedelta


# ============================================================
# ASTROXZ WALLPAPER CHANGER
# ============================================================

APP_NAME = "ASTROXZ Wallpaper Changer"

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CONFIG_PATH = os.path.join(BASE_DIR, "wallpaper_config.json")
UI_REQUEST_PATH = os.path.join(BASE_DIR, ".open_wallpaper_ui")

SUPPORTED_EXTENSIONS = (
    ".jpg",
    ".jpeg",
    ".png",
    ".bmp",
    ".gif",
    ".webp",
)


# ============================================================
# WINDOWS WALLPAPER API
# ============================================================

SPI_SETDESKWALLPAPER = 20
SPIF_UPDATEINIFILE = 0x01
SPIF_SENDCHANGE = 0x02


# ============================================================
# SINGLE INSTANCE
# ============================================================

MUTEX_NAME = "ASTROXZ_Wallpaper_Changer_FINAL_SINGLE_INSTANCE"

mutex_handle = None


def request_ui_open():
    try:
        with open(UI_REQUEST_PATH, "w", encoding="utf-8") as f:
            f.write("open")
        return True
    except Exception:
        return False


def acquire_single_instance():
    global mutex_handle

    kernel32 = ctypes.windll.kernel32

    mutex_handle = kernel32.CreateMutexW(
        None,
        False,
        MUTEX_NAME
    )

    ERROR_ALREADY_EXISTS = 183

    if kernel32.GetLastError() == ERROR_ALREADY_EXISTS:

        # Existing background instance should receive UI request
        if "--open-ui" in sys.argv:
            request_ui_open()

        return False

    return True


# ============================================================
# STARTUP
# ============================================================

STARTUP_FOLDER = os.path.join(
    os.environ.get(
        "APPDATA",
        os.path.expanduser("~")
    ),
    "Microsoft",
    "Windows",
    "Start Menu",
    "Programs",
    "Startup"
)

STARTUP_BAT = os.path.join(
    STARTUP_FOLDER,
    "ASTROXZ Wallpaper Changer.bat"
)


# ============================================================
# DEFAULT CONFIG
# ============================================================

DEFAULT_CONFIG = {
    "folder": "",
    "mode": "shuffle",
    "interval_value": 30,
    "interval_unit": "seconds",
    "exact_times": "",
    "startup": False,
}


# ============================================================
# CONFIG FUNCTIONS
# ============================================================

def load_config():
    if not os.path.exists(CONFIG_PATH):
        return DEFAULT_CONFIG.copy()

    try:
        with open(CONFIG_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)

        config = DEFAULT_CONFIG.copy()
        config.update(data)

        return config

    except Exception:
        return DEFAULT_CONFIG.copy()


def save_config(config):
    try:
        with open(CONFIG_PATH, "w", encoding="utf-8") as f:
            json.dump(
                config,
                f,
                indent=4
            )

        return True

    except Exception:
        return False


# ============================================================
# MAIN APP
# ============================================================

class WallpaperChanger:

    def __init__(self, root):

        self.root = root

        self.background_mode = "--background" in sys.argv

        self.config = load_config()

        # ----------------------------------------------------
        # Runtime state
        # ----------------------------------------------------

        self.wallpapers = []

        self.current_index = -1

        self.running = False

        self.timer_after_id = None

        self.next_change_time = None

        self.exact_next_timestamp = None

        # ----------------------------------------------------
        # Theme
        # ----------------------------------------------------

        self.bg = "#111111"
        self.panel = "#1a1a1a"
        self.panel2 = "#202020"
        self.fg = "#ffffff"
        self.muted = "#aaaaaa"
        self.accent = "#00d9ff"
        self.green = "#00ff88"
        self.red = "#ff5555"

        self.root.title(APP_NAME)

        self.root.configure(
            bg=self.bg
        )

        self.root.geometry("720x560")

        self.root.minsize(
            650,
            500
        )

        # ----------------------------------------------------
        # Variables
        # ----------------------------------------------------

        self.folder_var = tk.StringVar(
            value=self.config.get("folder", "")
        )

        self.mode_var = tk.StringVar(
            value=self.config.get("mode", "shuffle")
        )

        self.interval_value_var = tk.StringVar(
            value=str(
                self.config.get(
                    "interval_value",
                    30
                )
            )
        )

        self.interval_unit_var = tk.StringVar(
            value=self.config.get(
                "interval_unit",
                "seconds"
            )
        )

        self.exact_times_var = tk.StringVar(
            value=self.config.get(
                "exact_times",
                ""
            )
        )

        self.startup_var = tk.BooleanVar(
            value=self.config.get(
                "startup",
                False
            )
        )

        self.status_var = tk.StringVar(
            value="Ready"
        )

        self.countdown_var = tk.StringVar(
            value="Timer stopped"
        )

        # ----------------------------------------------------
        # Build UI
        # ----------------------------------------------------

        self.build_ui()

        # ----------------------------------------------------
        # UI request watcher
        #
        # The normal BAT creates:
        # .open_wallpaper_ui
        #
        # The background instance sees it and opens itself.
        # ----------------------------------------------------

        self.root.after(
            500,
            self.check_ui_request
        )

        # ----------------------------------------------------
        # BACKGROUND STARTUP
        #
        # IMPORTANT:
        # We do NOT call the normal start_scheduler()
        # here. Background startup has its own clean path.
        # ----------------------------------------------------

        if self.background_mode:

            self.root.withdraw()

            # Give Windows Explorer/Desktop time to initialize
            self.root.after(
                5000,
                self.background_startup
            )

    # ========================================================
    # UI
    # ========================================================

    def build_ui(self):

        # ----------------------------------------------------
        # Header
        # ----------------------------------------------------

        header = tk.Frame(
            self.root,
            bg=self.bg
        )

        header.pack(
            fill="x",
            padx=25,
            pady=(20, 10)
        )

        title = tk.Label(
            header,
            text="ASTROXZ WALLPAPER CHANGER",
            font=("Segoe UI", 18, "bold"),
            bg=self.bg,
            fg=self.accent
        )

        title.pack(
            anchor="w"
        )

        subtitle = tk.Label(
            header,
            text="Lightweight automatic wallpaper scheduler",
            font=("Segoe UI", 9),
            bg=self.bg,
            fg=self.muted
        )

        subtitle.pack(
            anchor="w",
            pady=(3, 0)
        )

        # ----------------------------------------------------
        # Main panel
        # ----------------------------------------------------

        main = tk.Frame(
            self.root,
            bg=self.panel
        )

        main.pack(
            fill="both",
            expand=True,
            padx=20,
            pady=10
        )

        # ----------------------------------------------------
        # Folder
        # ----------------------------------------------------

        tk.Label(
            main,
            text="Wallpaper Folder",
            font=("Segoe UI", 10, "bold"),
            bg=self.panel,
            fg=self.fg
        ).pack(
            anchor="w",
            padx=20,
            pady=(20, 5)
        )

        folder_row = tk.Frame(
            main,
            bg=self.panel
        )

        folder_row.pack(
            fill="x",
            padx=20
        )

        folder_entry = tk.Entry(
            folder_row,
            textvariable=self.folder_var,
            bg=self.panel2,
            fg=self.fg,
            insertbackground=self.fg,
            relief="flat",
            font=("Segoe UI", 10)
        )

        folder_entry.pack(
            side="left",
            fill="x",
            expand=True,
            ipady=7
        )

        tk.Button(
            folder_row,
            text="Browse",
            command=self.browse_folder,
            bg="#303030",
            fg=self.fg,
            activebackground="#404040",
            activeforeground=self.fg,
            relief="flat",
            padx=15
        ).pack(
            side="left",
            padx=(8, 0),
            ipady=5
        )

        # ----------------------------------------------------
        # Mode
        # ----------------------------------------------------

        tk.Label(
            main,
            text="Wallpaper Order",
            font=("Segoe UI", 10, "bold"),
            bg=self.panel,
            fg=self.fg
        ).pack(
            anchor="w",
            padx=20,
            pady=(20, 5)
        )

        mode_frame = tk.Frame(
            main,
            bg=self.panel
        )

        mode_frame.pack(
            anchor="w",
            padx=20
        )

        tk.Radiobutton(
            mode_frame,
            text="Shuffle",
            variable=self.mode_var,
            value="shuffle",
            bg=self.panel,
            fg=self.fg,
            selectcolor=self.panel2,
            activebackground=self.panel,
            activeforeground=self.fg
        ).pack(
            side="left",
            padx=(0, 25)
        )

        tk.Radiobutton(
            mode_frame,
            text="In Order",
            variable=self.mode_var,
            value="ordered",
            bg=self.panel,
            fg=self.fg,
            selectcolor=self.panel2,
            activebackground=self.panel,
            activeforeground=self.fg
        ).pack(
            side="left"
        )

        # ----------------------------------------------------
        # Interval
        # ----------------------------------------------------

        tk.Label(
            main,
            text="Change Interval",
            font=("Segoe UI", 10, "bold"),
            bg=self.panel,
            fg=self.fg
        ).pack(
            anchor="w",
            padx=20,
            pady=(20, 5)
        )

        interval_frame = tk.Frame(
            main,
            bg=self.panel
        )

        interval_frame.pack(
            anchor="w",
            padx=20
        )

        tk.Entry(
            interval_frame,
            textvariable=self.interval_value_var,
            width=10,
            bg=self.panel2,
            fg=self.fg,
            insertbackground=self.fg,
            relief="flat"
        ).pack(
            side="left",
            ipady=6
        )

        units = [
            "seconds",
            "minutes",
            "hours"
        ]

        tk.OptionMenu(
            interval_frame,
            self.interval_unit_var,
            *units
        ).pack(
            side="left",
            padx=(8, 0)
        )

        # ----------------------------------------------------
        # Exact times
        # ----------------------------------------------------

        tk.Label(
            main,
            text="Exact Times (optional)",
            font=("Segoe UI", 10, "bold"),
            bg=self.panel,
            fg=self.fg
        ).pack(
            anchor="w",
            padx=20,
            pady=(20, 5)
        )

        tk.Entry(
            main,
            textvariable=self.exact_times_var,
            bg=self.panel2,
            fg=self.fg,
            insertbackground=self.fg,
            relief="flat"
        ).pack(
            fill="x",
            padx=20,
            ipady=7
        )

        tk.Label(
            main,
            text="Example: 08:00, 12:30, 18:00, 22:00",
            font=("Segoe UI", 8),
            bg=self.panel,
            fg=self.muted
        ).pack(
            anchor="w",
            padx=20,
            pady=(3, 0)
        )

        # ----------------------------------------------------
        # Startup
        # ----------------------------------------------------

        tk.Checkbutton(
            main,
            text="Start automatically with Windows",
            variable=self.startup_var,
            command=self.toggle_startup,
            bg=self.panel,
            fg=self.fg,
            selectcolor=self.panel2,
            activebackground=self.panel,
            activeforeground=self.fg
        ).pack(
            anchor="w",
            padx=20,
            pady=(15, 5)
        )

        # ----------------------------------------------------
        # Status
        # ----------------------------------------------------

        status_frame = tk.Frame(
            main,
            bg=self.panel2
        )

        status_frame.pack(
            fill="x",
            padx=20,
            pady=(10, 10)
        )

        tk.Label(
            status_frame,
            textvariable=self.status_var,
            font=("Segoe UI", 10, "bold"),
            bg=self.panel2,
            fg=self.green
        ).pack(
            pady=(10, 2)
        )

        tk.Label(
            status_frame,
            textvariable=self.countdown_var,
            font=("Segoe UI", 12),
            bg=self.panel2,
            fg=self.fg
        ).pack(
            pady=(0, 10)
        )

        # ----------------------------------------------------
        # Buttons
        # ----------------------------------------------------

        button_frame = tk.Frame(
            main,
            bg=self.panel
        )

        button_frame.pack(
            fill="x",
            padx=20,
            pady=(5, 20)
        )

        tk.Button(
            button_frame,
            text="START",
            command=self.start_scheduler,
            bg=self.green,
            fg="#000000",
            activebackground="#00cc70",
            relief="flat",
            width=12,
            font=("Segoe UI", 9, "bold")
        ).pack(
            side="left",
            padx=(0, 8),
            ipady=5
        )

        tk.Button(
            button_frame,
            text="PAUSE",
            command=self.pause_scheduler,
            bg="#303030",
            fg=self.fg,
            activebackground="#404040",
            activeforeground=self.fg,
            relief="flat",
            width=12
        ).pack(
            side="left",
            padx=8,
            ipady=5
        )

        tk.Button(
            button_frame,
            text="NEXT",
            command=self.next_wallpaper,
            bg="#303030",
            fg=self.fg,
            activebackground="#404040",
            activeforeground=self.fg,
            relief="flat",
            width=12
        ).pack(
            side="left",
            padx=8,
            ipady=5
        )

        tk.Button(
            button_frame,
            text="HIDE",
            command=self.hide_window,
            bg="#303030",
            fg=self.fg,
            activebackground="#404040",
            activeforeground=self.fg,
            relief="flat",
            width=12
        ).pack(
            side="right",
            ipady=5
        )

        # ----------------------------------------------------
        # Countdown updater
        # ----------------------------------------------------

        self.root.after(
            250,
            self.update_countdown
        )

    # ========================================================
    # FOLDER
    # ========================================================

    def browse_folder(self):

        folder = filedialog.askdirectory()

        if folder:
            self.folder_var.set(folder)

            self.load_wallpapers()

    # ========================================================
    # LOAD WALLPAPERS
    # ========================================================

    def load_wallpapers(self):

        folder = self.folder_var.get().strip()

        if not folder or not os.path.isdir(folder):

            self.wallpapers = []

            self.current_index = -1

            return False

        try:

            files = []

            for name in os.listdir(folder):

                path = os.path.join(
                    folder,
                    name
                )

                if not os.path.isfile(path):
                    continue

                ext = os.path.splitext(
                    name
                )[1].lower()

                if ext in SUPPORTED_EXTENSIONS:

                    files.append(path)

            files.sort(
                key=lambda x: os.path.basename(x).lower()
            )

            if self.mode_var.get() == "shuffle":

                random.shuffle(files)

            self.wallpapers = files

            self.current_index = -1

            return len(files) > 0

        except Exception:

            self.wallpapers = []

            self.current_index = -1

            return False

    # ========================================================
    # SET WALLPAPER
    # ========================================================

    def set_wallpaper(self, path):

        try:

            result = ctypes.windll.user32.SystemParametersInfoW(
                SPI_SETDESKWALLPAPER,
                0,
                path,
                SPIF_UPDATEINIFILE | SPIF_SENDCHANGE
            )

            return bool(result)

        except Exception:

            return False

    # ========================================================
    # CHANGE WALLPAPER
    # ========================================================

    def change_wallpaper(self):

        if not self.wallpapers:

            if not self.load_wallpapers():

                return False

        if not self.wallpapers:

            return False

        # ----------------------------------------------------
        # Shuffle
        # ----------------------------------------------------

        if self.mode_var.get() == "shuffle":

            if len(self.wallpapers) == 1:

                index = 0

            else:

                choices = [
                    i
                    for i in range(len(self.wallpapers))
                    if i != self.current_index
                ]

                index = random.choice(
                    choices
                )

        # ----------------------------------------------------
        # Ordered
        # ----------------------------------------------------

        else:

            index = (
                self.current_index + 1
            ) % len(self.wallpapers)

        path = self.wallpapers[index]

        if self.set_wallpaper(path):

            self.current_index = index

            return True

        return False

    # ========================================================
    # INTERVAL
    # ========================================================

    def get_interval_seconds(self):

        try:

            value = float(
                self.interval_value_var.get().strip()
            )

            if value <= 0:

                return None

        except Exception:

            return None

        unit = self.interval_unit_var.get()

        if unit == "seconds":

            return value

        if unit == "minutes":

            return value * 60

        if unit == "hours":

            return value * 3600

        return None

    # ========================================================
    # EXACT TIME MODE
    # ========================================================

    def parse_exact_times(self):

        raw = self.exact_times_var.get().strip()

        if not raw:

            return []

        times = []

        for item in raw.split(","):

            item = item.strip()

            if not item:
                continue

            try:

                dt = datetime.strptime(
                    item,
                    "%H:%M"
                )

                times.append(
                    dt.time()
                )

            except ValueError:

                return None

        times.sort(
            key=lambda x: (
                x.hour,
                x.minute
            )
        )

        return times

    def using_exact_time_mode(self):

        return bool(
            self.exact_times_var.get().strip()
        )

    def get_next_exact_datetime(self):

        times = self.parse_exact_times()

        if times is None or not times:

            return None

        now = datetime.now()

        candidates = []

        for t in times:

            candidate = datetime.combine(
                now.date(),
                t
            )

            if candidate > now:

                candidates.append(
                    candidate
                )

        if candidates:

            return min(candidates)

        # No time left today -> first time tomorrow

        tomorrow = now.date() + timedelta(
            days=1
        )

        return datetime.combine(
            tomorrow,
            times[0]
        )

    # ========================================================
    # TIMER
    # ========================================================

    def cancel_timer(self):

        if self.timer_after_id is not None:

            try:

                self.root.after_cancel(
                    self.timer_after_id
                )

            except Exception:
                pass

            self.timer_after_id = None

    def schedule_next_change(self):

        self.cancel_timer()

        if not self.running:

            return

        # ----------------------------------------------------
        # EXACT TIME
        # ----------------------------------------------------

        if self.using_exact_time_mode():

            next_time = self.get_next_exact_datetime()

            if next_time is None:

                self.running = False

                self.next_change_time = None

                self.exact_next_timestamp = None

                self.status_var.set(
                    "Invalid exact times"
                )

                self.countdown_var.set(
                    "Timer stopped"
                )

                return

            self.exact_next_timestamp = (
                next_time.timestamp()
            )

            self.next_change_time = None

            delay_seconds = (
                self.exact_next_timestamp
                - time.time()
            )

        # ----------------------------------------------------
        # INTERVAL
        # ----------------------------------------------------

        else:

            seconds = self.get_interval_seconds()

            if seconds is None:

                self.running = False

                self.next_change_time = None

                self.exact_next_timestamp = None

                self.status_var.set(
                    "Invalid interval"
                )

                self.countdown_var.set(
                    "Timer stopped"
                )

                return

            self.next_change_time = (
                time.monotonic()
                + seconds
            )

            self.exact_next_timestamp = None

            delay_seconds = seconds

        delay_ms = max(
            1,
            int(delay_seconds * 1000)
        )

        # Windows/Tk maximum delay protection
        delay_ms = min(
            delay_ms,
            2147483647
        )

        self.timer_after_id = self.root.after(
            delay_ms,
            self.timer_finished
        )

    # ========================================================
    # TIMER FINISHED
    # ========================================================

    def timer_finished(self):

        self.timer_after_id = None

        if not self.running:

            return

        success = self.change_wallpaper()

        if success:

            self.status_var.set(
                "Running"
            )

        else:

            self.status_var.set(
                "Waiting for Windows..."
            )

        # ----------------------------------------------------
        # ALWAYS schedule the next change
        # ----------------------------------------------------

        self.schedule_next_change()

    # ========================================================
    # NORMAL START
    # ========================================================

    def start_scheduler(self):

        # If somehow called while background startup is active,
        # let the dedicated background function handle it.
        if self.background_mode:

            self.background_startup()

            return

        self.cancel_timer()

        self.next_change_time = None

        self.exact_next_timestamp = None

        if not self.load_wallpapers():

            self.running = False

            self.status_var.set(
                "No wallpapers found"
            )

            self.countdown_var.set(
                "Timer stopped"
            )

            return

        # ----------------------------------------------------
        # Validate exact time mode
        # ----------------------------------------------------

        if self.using_exact_time_mode():

            if not self.parse_exact_times():

                self.running = False

                self.status_var.set(
                    "Invalid exact times"
                )

                self.countdown_var.set(
                    "Timer stopped"
                )

                return

        # ----------------------------------------------------
        # Validate interval mode
        # ----------------------------------------------------

        else:

            if self.get_interval_seconds() is None:

                self.running = False

                self.status_var.set(
                    "Invalid interval"
                )

                self.countdown_var.set(
                    "Timer stopped"
                )

                return

        # ----------------------------------------------------
        # Save settings
        # ----------------------------------------------------

        self.save_current_settings()

        # ----------------------------------------------------
        # Start
        # ----------------------------------------------------

        self.running = True

        success = self.change_wallpaper()

        if success:

            self.status_var.set(
                "Running"
            )

        else:

            self.status_var.set(
                "Waiting for Windows..."
            )

        self.schedule_next_change()

    # ========================================================
    # BACKGROUND STARTUP
    #
    # This is the important fixed section.
    #
    # Startup process:
    #
    # Windows
    #    ↓
    # wait 5 sec
    #    ↓
    # load wallpapers
    #    ↓
    # running = True
    #    ↓
    # set wallpaper
    #    ↓
    # schedule timer
    #
    # If Windows isn't ready:
    #    retry after 2 sec
    # ========================================================

    def background_startup(self):

        if not self.background_mode:

            return

        # ----------------------------------------------------
        # Don't accidentally start multiple startup routines
        # ----------------------------------------------------

        if self.running:

            if self.timer_after_id is None:

                self.schedule_next_change()

            return

        # ----------------------------------------------------
        # Load wallpapers
        # ----------------------------------------------------

        if not self.load_wallpapers():

            self.running = True

            self.status_var.set(
                "Waiting for wallpapers..."
            )

            self.root.after(
                3000,
                self.background_startup
            )

            return

        # ----------------------------------------------------
        # Validate timing settings
        # ----------------------------------------------------

        if self.using_exact_time_mode():

            if not self.parse_exact_times():

                self.running = False

                self.status_var.set(
                    "Invalid exact times"
                )

                self.countdown_var.set(
                    "Timer stopped"
                )

                return

        else:

            if self.get_interval_seconds() is None:

                self.running = False

                self.status_var.set(
                    "Invalid interval"
                )

                self.countdown_var.set(
                    "Timer stopped"
                )

                return

        # ----------------------------------------------------
        # START RUNNING
        # ----------------------------------------------------

        self.running = True

        # ----------------------------------------------------
        # Try wallpaper
        # ----------------------------------------------------

        success = self.change_wallpaper()

        if success:

            self.status_var.set(
                "Running"
            )

            # ------------------------------------------------
            # IMPORTANT:
            # Timer is scheduled immediately here.
            # ------------------------------------------------

            self.schedule_next_change()

        else:

            self.status_var.set(
                "Waiting for Windows..."
            )

            # Don't schedule the wallpaper timer yet.
            # Windows desktop isn't ready.
            #
            # Retry the wallpaper itself.

            self.root.after(
                2000,
                self.background_startup_retry
            )

    # ========================================================
    # BACKGROUND RETRY
    # ========================================================

    def background_startup_retry(self):

        if not self.background_mode:

            return

        if not self.running:

            return

        success = self.change_wallpaper()

        if success:

            self.status_var.set(
                "Running"
            )

            self.schedule_next_change()

        else:

            self.status_var.set(
                "Waiting for Windows..."
            )

            self.root.after(
                2000,
                self.background_startup_retry
            )

    # ========================================================
    # PAUSE
    # ========================================================

    def pause_scheduler(self):

        self.running = False

        self.cancel_timer()

        self.next_change_time = None

        self.exact_next_timestamp = None

        self.status_var.set(
            "Paused"
        )

        self.countdown_var.set(
            "Timer stopped"
        )

    # ========================================================
    # NEXT
    # ========================================================

    def next_wallpaper(self):

        if not self.wallpapers:

            if not self.load_wallpapers():

                self.status_var.set(
                    "No wallpapers found"
                )

                return

        success = self.change_wallpaper()

        if success:

            if self.running:

                self.schedule_next_change()

                self.status_var.set(
                    "Running"
                )

            else:

                self.status_var.set(
                    "Wallpaper changed"
                )

        else:

            self.status_var.set(
                "Wallpaper change failed"
            )

    # ========================================================
    # COUNTDOWN
    # ========================================================

    def update_countdown(self):

        try:

            if self.running:

                remaining = None

                # --------------------------------------------
                # Exact time
                # --------------------------------------------

                if (
                    self.exact_next_timestamp
                    is not None
                ):

                    remaining = (
                        self.exact_next_timestamp
                        - time.time()
                    )

                # --------------------------------------------
                # Interval
                # --------------------------------------------

                elif (
                    self.next_change_time
                    is not None
                ):

                    remaining = (
                        self.next_change_time
                        - time.monotonic()
                    )

                # --------------------------------------------
                # Display
                # --------------------------------------------

                if remaining is not None:

                    remaining = max(
                        0,
                        int(remaining)
                    )

                    hours = remaining // 3600

                    minutes = (
                        remaining % 3600
                    ) // 60

                    seconds = (
                        remaining % 60
                    )

                    if hours > 0:

                        self.countdown_var.set(
                            f"Next wallpaper in "
                            f"{hours:02d}:"
                            f"{minutes:02d}:"
                            f"{seconds:02d}"
                        )

                    else:

                        self.countdown_var.set(
                            f"Next wallpaper in "
                            f"{minutes:02d}:"
                            f"{seconds:02d}"
                        )

                else:

                    self.countdown_var.set(
                        "Starting..."
                    )

            else:

                self.countdown_var.set(
                    "Timer stopped"
                )

        except Exception:

            pass

        self.root.after(
            250,
            self.update_countdown
        )

    # ========================================================
    # STARTUP TOGGLE
    # ========================================================

    def toggle_startup(self):

        if self.startup_var.get():

            self.enable_startup()

        else:

            self.disable_startup()

        self.save_current_settings()

    def enable_startup(self):

        try:

            os.makedirs(
                STARTUP_FOLDER,
                exist_ok=True
            )

            # ------------------------------------------------
            # Locate pythonw.exe
            # ------------------------------------------------

            python_dir = os.path.dirname(
                sys.executable
            )

            pythonw_path = os.path.join(
                python_dir,
                "pythonw.exe"
            )

            if not os.path.exists(
                pythonw_path
            ):

                pythonw_path = sys.executable

            script_path = os.path.abspath(
                __file__
            )

            # ------------------------------------------------
            # Startup BAT
            # ------------------------------------------------

            bat_content = (
                "@echo off\r\n"
                f'start "" "{pythonw_path}" "{script_path}" --background\r\n'
                "exit\r\n"
            )

            with open(
                STARTUP_BAT,
                "w",
                encoding="utf-8"
            ) as f:

                f.write(
                    bat_content
                )

            self.startup_var.set(
                True
            )

            self.status_var.set(
                "Windows startup enabled"
            )

        except Exception as e:

            self.startup_var.set(
                False
            )

            messagebox.showerror(
                APP_NAME,
                f"Could not enable startup:\n\n{e}"
            )

    def disable_startup(self):

        try:

            if os.path.exists(
                STARTUP_BAT
            ):

                os.remove(
                    STARTUP_BAT
                )

            self.startup_var.set(
                False
            )

            self.status_var.set(
                "Windows startup disabled"
            )

        except Exception as e:

            messagebox.showerror(
                APP_NAME,
                f"Could not disable startup:\n\n{e}"
            )

    # ========================================================
    # SAVE SETTINGS
    # ========================================================

    def save_current_settings(self):

        config = {
            "folder": self.folder_var.get(),
            "mode": self.mode_var.get(),
            "interval_value": self.interval_value_var.get(),
            "interval_unit": self.interval_unit_var.get(),
            "exact_times": self.exact_times_var.get(),
            "startup": self.startup_var.get(),
        }

        save_config(
            config
        )

    # ========================================================
    # HIDE
    # ========================================================

    def hide_window(self):

        self.save_current_settings()

        # IMPORTANT:
        # Hide does NOT stop scheduler.

        self.root.withdraw()

    # ========================================================
    # UI REQUEST
    #
    # Existing background instance receives request from:
    #
    # wallpaper_changer.pyw --open-ui
    #
    # ========================================================

    def check_ui_request(self):

        try:

            if os.path.exists(
                UI_REQUEST_PATH
            ):

                try:

                    os.remove(
                        UI_REQUEST_PATH
                    )

                except Exception:

                    pass

                # ------------------------------------------------
                # Switch from hidden background mode to UI mode
                # ------------------------------------------------

                self.background_mode = False

                self.root.deiconify()

                self.root.lift()

                self.root.attributes(
                    "-topmost",
                    True
                )

                self.root.after(
                    150,
                    lambda: self.root.attributes(
                        "-topmost",
                        False
                    )
                )

                self.root.focus_force()

                if self.running:

                    self.status_var.set(
                        "Running"
                    )

                    # Safety:
                    # If somehow timer disappeared, recreate it.
                    if self.timer_after_id is None:

                        self.schedule_next_change()

                else:

                    self.status_var.set(
                        "Paused"
                    )

        except Exception:

            pass

        self.root.after(
            500,
            self.check_ui_request
        )

    # ========================================================
    # CLOSE
    # ========================================================

    def on_close(self):

        # X actually stops the scheduler.

        self.save_current_settings()

        self.running = False

        self.cancel_timer()

        self.next_change_time = None

        self.exact_next_timestamp = None

        try:

            if os.path.exists(
                UI_REQUEST_PATH
            ):

                os.remove(
                    UI_REQUEST_PATH
                )

        except Exception:

            pass

        self.root.destroy()


# ============================================================
# MAIN
# ============================================================

def main():

    # --------------------------------------------------------
    # SINGLE INSTANCE
    # --------------------------------------------------------

    if not acquire_single_instance():

        # Existing instance received --open-ui signal.
        #
        # Nothing else needs to happen.
        #
        # The existing instance will see the request file.

        return

    # --------------------------------------------------------
    # Remove stale UI request when launching normally
    # --------------------------------------------------------

    if "--background" not in sys.argv:

        try:

            if os.path.exists(
                UI_REQUEST_PATH
            ):

                os.remove(
                    UI_REQUEST_PATH
                )

        except Exception:

            pass

    # --------------------------------------------------------
    # Tk
    # --------------------------------------------------------

    root = tk.Tk()

    app = WallpaperChanger(
        root
    )

    root.protocol(
        "WM_DELETE_WINDOW",
        app.on_close
    )

    root.mainloop()


# ============================================================
# RUN
# ============================================================

if __name__ == "__main__":

    main()