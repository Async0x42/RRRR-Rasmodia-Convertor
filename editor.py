# path/filename: update_display_script.py
import json5
from rich.console import Console
from rich.table import Table

def load_json(filename):
    """Load JSON data from a file."""
    with open(filename, 'r') as file:
        return json5.load(file)

def find_differences(original, patched):
    """Compare two dictionaries and find differences."""
    diffs = []
    for key in patched:
        if original.get(key, None) != patched[key]:  # Only add differences
            original_value = original.get(key, '')
            patched_value = patched[key]
            diffs.append((key, f"{key}: {original_value}", f"{key}: {patched_value}"))
    return diffs

class ProgressDisplay:
    """Class to display progress of operations in a table format."""
    def __init__(self, total, console):
        self.total = total
        self.current = 0
        self.console = console
        self.table = Table()

    def update_progress(self, current, key, o_text, p_text):
        """Update the progress displayed on the console."""
        self.current = current
        self.console.clear()
        self.table.columns = []
        self.table.add_column("Key", justify="right")
        self.table.add_column("Text", justify="left")
        self.table.rows = []  # Clear previous rows
        self.table.add_row(highlight_key(key), highlight_differences(o_text, p_text))
        self.table.add_row("[bold blue]Diff Progress:[/bold blue]", f"[dark_blue]{self.current}/{self.total}[/dark_blue]")
        self.console.print(self.table)

def highlight_key(original):
    """Apply syntax highlighting to differences between texts."""
    from rich.text import Text

    highlighted_text = Text()
    highlighted_text.append(original + ':', style="bold blue")
    return highlighted_text

def highlight_differences(original, patched):
    """Apply syntax highlighting to differences between texts."""
    from rich.text import Text
    original_key, original_rest = original.split(':', 1)
    patched_key, patched_rest = patched.split(':', 1)

    highlighted_text = Text()
    original_words = original_rest.strip().split()
    patched_words = patched_rest.strip().split()
    
    for o_word, p_word in zip(original_words, patched_words):
        if o_word != p_word:
            highlighted_text.append(o_word, style="red strike").append(' ')
            highlighted_text.append(p_word + ' ', style="green")
        else:
            highlighted_text.append(o_word+ ' ', style="default")
    return highlighted_text

def setup_console(diffs):
    """Set up and display the console with progress and differences."""
    console = Console()
    progress = ProgressDisplay(len(diffs), console)

    index = 0
    while True:  # Using a continuous loop to allow indefinite navigation
        key, o_text, p_text = diffs[index]
        progress.update_progress(index + 1, key, o_text, p_text)
        key = console.input("[bold blue]Navigate with '.', ',' or 'q' to quit:[/bold blue] ").strip().lower()
        
        if key == 'q':
            break  # Exit the loop if 'q' is pressed
        elif key == ',':
            index = (index - 1) % len(diffs)  # Wrap around to the last index if at first
        elif key == '.':
            index = (index + 1) % len(diffs)  # Wrap around to the first index if at last



def main():
    """Main function to load data and show differences."""
    original_data = load_json('data/default.json')
    patched_data = load_json('data/output.json')
    diffs = find_differences(original_data, patched_data)
    if not diffs:
        print("[bold red]No differences to display.[/bold red]")
        return
    else:
        setup_console(diffs)

if __name__ == "__main__":
    main()
