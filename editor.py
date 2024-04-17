import json5
from rich.console import Console
from rich.text import Text
import sys

# Step 1: Define a function to load JSON data from files
def load_json(filename):
    with open(filename, 'r') as file:
        return json5.load(file)

# Step 2: Define a function to compare two dictionaries and return differences
def find_differences(original, patched):
    diffs = []
    for key in patched:
        original_text = f"{key}: {original.get(key, '')}"
        patched_text = f"{key}: {patched[key]}"
        diffs.append((original_text, patched_text))
    return diffs

# Step 3: Function to setup the console and input handling
def setup_console(diffs):
    console = Console()
    index = 0

    def show_diff():
        console.clear()
        o_text, p_text = diffs[index]
        console.print("[red]" + o_text + "[/red]")
        console.print("[green]" + p_text + "[/green]")

    show_diff()

    while True:
        key = console.input("[bold blue]Use arrow keys to navigate or 'q' to quit: [/bold blue]").strip().lower()
        if key == 'q':
            break
        elif key == '.' and index < len(diffs) - 1:
            index += 1
            show_diff()
        elif key == ',' and index > 0:
            index -= 1
            show_diff()

# Main execution function
def main():
    original_data = load_json('data/default.json')
    patched_data = load_json('data/output.json')
    diffs = find_differences(original_data, patched_data)
    setup_console(diffs)

if __name__ == "__main__":
    main()
