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
    """
    Reads a CSV or Excel file and returns a Pandas DataFrame. Throws an error for unsupported files.
    """
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
    """
    Displays combined stats summary table and type breakdown for both files.
    The stats parameter is a dict keyed by filename containing loaded info.
    """
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


def remove_blank_majority_rows(df, fname):
    non_blank_counts = df.notna().sum(axis=1)
    keep_mask = non_blank_counts >= (len(df.columns) / 2)
    result = df[keep_mask].copy()
    removed = len(df) - len(result)
    console.print(
        Panel(
            f"[bold green]{fname}: {removed} rows removed. {len(result)} rows remaining.[/bold green]",
            title="Majority Blank Row Removal",
            subtitle_align="right",
            style="on magenta"
        )
    )
    return result


def count_special_characters(df, fname):
    special_char_pattern = re.compile(r'[^A-Za-z0-9\s]')

    def row_has_special(series):
        return series.astype(str).apply(lambda x: bool(special_char_pattern.search(x))).any()

    mask = df.apply(row_has_special, axis=1)
    count = mask.sum()
    console.print(
        Panel(
            f"[bold yellow]{fname}: {count} rows contain special characters.[/bold yellow]",
            title="Special Character Count",
            subtitle_align="right",
            style="on cyan"
        )
    )
    return count


def compare_dataframes(source, target):
    join_cols = list(source.columns)
    console.print(Panel(
        f"[bold white]Comparing on columns: {join_cols}[/bold white]",
        title="Comparison Keys",
        style="bold magenta"
    ))
    merged = source.merge(target, how='outer', indicator=True)
    only_source = merged[merged['_merge'] == 'left_only']
    only_target = merged[merged['_merge'] == 'right_only']
    only_source.to_csv('only_in_source.csv', index=False)
    only_target.to_csv('only_in_target.csv', index=False)

    comp_table = Table(title="Comparison Summary", box=box.ASCII)
    comp_table.add_column("Category", style="blue")
    comp_table.add_column("Count", style="red")
    comp_table.add_row("Source Total", str(len(source)))
    comp_table.add_row("Target Total", str(len(target)))
    comp_table.add_row("Source Only", str(len(only_source)))
    comp_table.add_row("Target Only", str(len(only_target)))
    console.print(Panel(comp_table, title="Data Comparison Result", style="bold green"))

    console.print(f"[bold green]Source-only records exported to only_in_source.csv[/bold green]")
    console.print(f"[bold red]Target-only records exported to only_in_target.csv[/bold red]")


if __name__ == "__main__":
    file_stats = {}

    src_path = Prompt.ask("[bold blue]Enter path for source file (.csv/.xlsx)[/bold blue]")
    tgt_path = Prompt.ask("[bold blue]Enter path for target file (.csv/.xlsx)[/bold blue]")

    try:
        src_df, src_time, src_size = read_file(src_path)
        tgt_df, tgt_time, tgt_size = read_file(tgt_path)
        file_stats[src_path] = {'df': src_df, 'elapsed': src_time, 'size': src_size}
        file_stats[tgt_path] = {'df': tgt_df, 'elapsed': tgt_time, 'size': tgt_size}
    except Exception as e:
        console.print(f"[bold red]Error: {e}[/bold red]")
        exit(1)

    get_file_stats_summary(file_stats)

    console.print("\n[bold yellow]Which reconciliation do you want?[/bold yellow]")
    options_table = Table(title="Options", box=box.ROUNDED)
    options_table.add_column("Number", style="green")
    options_table.add_column("Description", style="bold magenta")
    options_table.add_row("1", "Data comparison")
    options_table.add_row("2", "Remove rows where majority of columns are blank")
    options_table.add_row("3", "Count rows which include special character")
    console.print(options_table)

    choice = Prompt.ask("Enter 1, 2, or 3", choices=["1", "2", "3"], default="1")

    if choice == "1":
        compare_dataframes(src_df, tgt_df)
    elif choice == "2":
        remove_blank_majority_rows(src_df, src_path)
        remove_blank_majority_rows(tgt_df, tgt_path)
    elif choice == "3":
        count_special_characters(src_df, src_path)
        count_special_characters(tgt_df, tgt_path)
