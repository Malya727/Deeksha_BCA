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
    console.print("\n---\n")  # Newline item indicator for clean display


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
    console.print("\n---\n")  # Newline item indicator for clean display
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
    console.print("\n---\n")  # Newline item indicator for clean display
    return count


def safe_filename(filepath):
    base = os.path.basename(filepath)
    name, _ = os.path.splitext(base)
    return name


def compare_dataframes(source_df, target_df, src_fname, tgt_fname):
    # Normalize column names (strip spaces and lower case) for robust matching
    source_df.columns = source_df.columns.str.strip().str.lower()
    target_df.columns = target_df.columns.str.strip().str.lower()

    # Identify common columns regardless of order, case, or extra spaces
    common_cols = list(set(source_df.columns).intersection(set(target_df.columns)))

    if not common_cols:
        console.print("[bold red]No common columns found for comparison after normalization![/bold red]")
        return

    console.print(Panel(f"[bold white]Comparing on columns (order & case agnostic): {common_cols}[/bold white]",
                        title="Comparison Keys", style="bold magenta"))

    # Select only common columns and sort rows by these columns for aligned comparison
    source_sub = source_df[common_cols].copy().sort_values(by=common_cols).reset_index(drop=True)
    target_sub = target_df[common_cols].copy().sort_values(by=common_cols).reset_index(drop=True)

    merged = source_sub.merge(target_sub, how='outer', indicator=True)

    only_source = merged[merged['_merge'] == 'left_only'].drop(columns=['_merge'])
    only_target = merged[merged['_merge'] == 'right_only'].drop(columns=['_merge'])

    only_source_fname = f"{safe_filename(src_fname)}_only_in_source.csv"
    only_target_fname = f"{safe_filename(tgt_fname)}_only_in_target.csv"

    only_source.to_csv(only_source_fname, index=False)
    only_target.to_csv(only_target_fname, index=False)

    comp_table = Table(title="Comparison Summary", box=box.ASCII)
    comp_table.add_column("Category", style="blue")
    comp_table.add_column("Count", style="red")
    comp_table.add_row("Source Total", str(len(source_sub)))
    comp_table.add_row("Target Total", str(len(target_sub)))
    comp_table.add_row("Source Only", str(len(only_source)))
    comp_table.add_row("Target Only", str(len(only_target)))
    console.print(Panel(comp_table, title="Data Comparison Result", style="bold green"))

    console.print(f"[bold green]Records only in source saved to: {only_source_fname}[/bold green]")
    console.print(f"[bold red]Records only in target saved to: {only_target_fname}[/bold red]")
    console.print("\n---\n")


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
        compare_dataframes(src_df, tgt_df, src_path, tgt_path)
    elif choice == "2":
        remove_blank_majority_rows(src_df, src_path)
        remove_blank_majority_rows(tgt_df, tgt_path)
    elif choice == "3":
        count_special_characters(src_df, src_path)
        count_special_characters(tgt_df, tgt_path)
