import os
import time
import pandas as pd
import numpy as np
import re
from rich.console import Console
from rich.prompt import Prompt
from rich.table import Table
from rich.panel import Panel
from rich import box

console = Console()


def read_file(filepath):
    if not (filepath.lower().endswith('.csv') or filepath.lower().endswith('.xlsx')):
        console.print(f"[bold red]Invalid file type: {filepath} (Only .csv or .xlsx supported)[/bold red]")
        raise ValueError(f"Invalid file type: {filepath}")
    start_time = time.time()
    if filepath.lower().endswith('.csv'):
        df = pd.read_csv(filepath)
    else:
        df = pd.read_excel(filepath)
    elapsed = time.time() - start_time
    size = os.path.getsize(filepath)
    return df, elapsed, size


def get_file_stats_summary(stats):
    summary_table = Table(show_header=True, header_style="bold green", box=box.SIMPLE)
    summary_table.add_column("File", style="yellow")
    summary_table.add_column("Read Time (s)", justify="right", style="cyan")
    summary_table.add_column("Size (KB)", justify="right", style="magenta")
    summary_table.add_column("Columns", justify="right", style="magenta")
    summary_table.add_column("Rows", justify="right", style="magenta")

    dtype_table = Table(title="Column Type Breakdown for Each File", show_lines=True, box=box.MINIMAL_DOUBLE_HEAD)
    dtype_table.add_column("File", style="yellow")
    dtype_table.add_column("Type", style="cyan")
    dtype_table.add_column("Count", style="magenta")

    for fname, info in stats.items():
        summary_table.add_row(
            fname,
            f"{info['elapsed']:.2f}",
            f"{info['size'] / 1024:.2f}",
            str(info['df'].shape[1]),
            str(info['df'].shape[0])
        )
        dtype_counts = info['df'].dtypes.value_counts()
        for dtype, cnt in dtype_counts.items():
            dtype_table.add_row(fname, str(dtype), str(cnt))

    console.print(Panel(summary_table, title="Files Statistics Summary", subtitle_align="right", style="bold blue"))
    console.print(dtype_table)
    console.print("\n---\n")  # Newline item indicator for clean
