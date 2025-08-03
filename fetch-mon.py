import os
import psutil
import platform
import datetime
import subprocess
import time
from shutil import get_terminal_size
from rich.live import Live
from rich.console import Console, Group
from rich.table import Table
from rich.panel import Panel
from rich.progress import Progress, TextColumn, ProgressColumn
from rich.text import Text
from rich.align import Align

console = Console()

ASCII_LOGO = r"""  
⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⣸⣇⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢰⣿⣿⡆⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢠⣿⣿⣿⣿⡄⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢿⣿⣿⣿⣿⣿⡄⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
⠀⠀⠀⠀⠀⠀⠀⠀⠀⢀⣷⣤⣙⢻⣿⣿⣿⣿⡀⠀⠀⠀⠀⠀⠀⠀⠀⠀
⠀⠀⠀⠀⠀⠀⠀⠀⢀⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⡀⠀⠀⠀⠀⠀⠀⠀⠀
⠀⠀⠀⠀⠀⠀⠀⢠⣾⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣷⡄⠀⠀⠀⠀⠀⠀⠀
⠀⠀⠀⠀⠀⠀⢠⣿⣿⣿⣿⣿⡿⠛⠛⠿⣿⣿⣿⣿⣿⡄⠀⠀⠀⠀⠀⠀
⠀⠀⠀⠀⠀⢠⣿⣿⣿⣿⣿⠏⠀⠀⠀⠀⠙⣿⣿⣿⣿⣿⡄⠀⠀⠀⠀⠀
⠀⠀⠀⠀⣰⣿⣿⣿⣿⣿⣿⠀⠀⠀⠀⠀⠀⢿⣿⣿⣿⣿⠿⣆⠀⠀⠀⠀
⠀⠀⠀⣴⣿⣿⣿⣿⣿⣿⣿⠀⠀⠀⠀⠀⠀⣿⣿⣿⣿⣿⣷⣦⡀⠀⠀⠀
⠀⢀⣾⣿⣿⠿⠟⠛⠋⠉⠉⠀⠀⠀⠀⠀⠀⠉⠉⠙⠛⠻⠿⣿⣿⣷⡀⠀
⣠⠟⠋⠁⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠈⠙⠻⣄
"""

class UsageBar(ProgressColumn):
    def render(self, task):
        bar = "█" * int(task.percentage / 10) + "░" * (10 - int(task.percentage / 10))
        return Text(f"{bar} {task.percentage:.1f}%")

def get_uptime():
    uptime_seconds = time.time() - psutil.boot_time()
    return str(datetime.timedelta(seconds=int(uptime_seconds)))

def get_temperature():
    temps = psutil.sensors_temperatures()
    if not temps:
        return "N/A"
    for name, entries in temps.items():
        for entry in entries:
            if entry.label in ("Package id 0", ""):
                return f"{entry.current:.1f}°C"
    return "N/A"

def build_cpu_table():
    cpu_percents = psutil.cpu_percent(percpu=True, interval=0.1)
    cpu_table = Table.grid(padding=(0, 2))
    for i in range(0, len(cpu_percents), 4):
        row = []
        for j in range(4):
            if i + j < len(cpu_percents):
                pct = cpu_percents[i + j]
                bar = "█" * int(pct / 10) + "░" * (10 - int(pct / 10))
                row.append(Text(f"Core {i+j}: {bar} {pct:.1f}%  ", style="bold blue"))
            else:
                row.append(Text(""))
        cpu_table.add_row(*row)
        cpu_table.add_row()
    return cpu_table

def build_mem_disk_progress():
    progress = Progress(
        expand=True
    )
    mem = psutil.virtual_memory()
    disk = psutil.disk_usage('/')
    progress.add_task("mem", total=100, completed=mem.percent)
    progress.add_task("disk", total=100, completed=disk.percent)
    return mem.total, disk.total, mem.percent, disk.percent, progress

def render_dashboard():
    os_name, os_version, hostname = platform.system(), platform.release(), platform.node()
    uptime = get_uptime()
    temp = get_temperature()

    width = min(get_terminal_size((100, 20)).columns - 4, 120)

    cpu_table = build_cpu_table()
    mem_total, disk_total, mem_pct, disk_pct, memdisk_progress = build_mem_disk_progress()

    usage_group = Group(
        Text.from_markup(
            f""
            f"[bold]Host:[/] {hostname}\n\n"
            f"[bold]OS:[/] {os_name} {os_version}\n\n"
            f"[bold]Uptime:[/] {uptime}\n\n"
            f"[bold]Temp:[/] {temp}\n\n"
            f"\n[bold]CPU Usage:[/]"
        ),
        cpu_table,
        Text.from_markup(f"\n[bold]MEM: {mem_total//(1024**3)} GB | DISK: {disk_total//(1024**3)} GB[/] "),
        memdisk_progress
    )

    combined_table = Table.grid(padding=(0, 2))
    combined_table.add_row(Text(ASCII_LOGO, style="bold blue"), usage_group)

    layout = Align.center(combined_table, vertical="middle", width=width)

    return Align.center(layout, vertical="middle")

psutil.cpu_percent(percpu=True)

with Live(render_dashboard(), refresh_per_second=1, screen=True) as live:
    while True:
        time.sleep(1)
        live.update(render_dashboard())
