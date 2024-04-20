import json5
from rich.console import Console
from rich.table import Table
from rich.text import Text
from prompt_toolkit import PromptSession
from prompt_toolkit.shortcuts import prompt
import os

def load_json(filename):
    """Load JSON data from a file."""
    with open(filename, 'r') as file:
        return json5.load(file)

def save_json(data, filename):
    """Save JSON data to a file."""
    with open(filename, 'w') as file:
        json5.dump(data, file, indent=4)

def apply_corrections(data, corrections):
    """Apply corrections on top of the original data."""
    corrected_data = data.copy()
    corrected_data.update(corrections)
    return corrected_data

def find_differences(original, patched, corrections=None):
    """Compare two dictionaries and find differences."""
    diffs = []
    for key in patched:
        if original.get(key, None) != patched[key]:
            original_value = original.get(key, '')
            patched_value = patched[key]
            corrected = key in corrections if corrections else False
            diffs.append((key, original_value, patched_value, corrected))
    return diffs

class ProgressDisplay:
    """Display progress of operations in a table format."""
    def __init__(self, total, console):
        self.total = total
        self.current = 0
        self.console = console
        self.table = Table()

    def update_progress(self, current, key, o_text, p_text, corrected):
        """Update the progress displayed on the console."""
        self.current = current
        self.console.clear()
        self.table.columns = []
        self.table.add_column("Key", justify="right")
        self.table.add_column("Text", justify="left")
        self.table.rows = []
        self.table.add_row(highlight_key(key), highlight_differences(o_text, p_text))
        self.table.add_row("[bold blue]Diff Progress:[/bold blue]", f"[dark_blue]{self.current}/{self.total}[/dark_blue]")
        if corrected:
            self.table.add_row("[bold]Status:[/bold]", "[bold green]ACCEPTED/CORRECTED[/bold green]")
        else:
            self.table.add_row("[bold]Status:[/bold]", "[bold red]UNCONFIRMED[/bold red]")
        self.console.print(self.table)

def highlight_key(key):
    """Syntax highlighting for a key."""
    return Text(key + ':', style="bold blue")

def highlight_differences(original, patched):
    """Highlight differences between texts."""
    highlighted_text = Text()
    original_words = original.strip().split()
    patched_words = patched.strip().split()

    for o_word, p_word in zip(original_words, patched_words):
        if o_word != p_word:
            highlighted_text.append(o_word, style="red strike").append(' ')
            highlighted_text.append(p_word + ' ', style="green")
        else:
            highlighted_text.append(o_word + ' ', style="default")
    return highlighted_text

def edit_text(text):
    """Prepopulate and allow editing of text with cursor control."""
    session = PromptSession()
    def pre_run():
        session.app.current_buffer.cursor_position = text.find('[') if '[' in text else 0
    return session.prompt("[bold blue]Edit text:[/bold blue] ", default=text, pre_run=pre_run)

def find_first_unconfirmed(diffs):
    """Find the index of the first unconfirmed difference."""
    for i, diff in enumerate(diffs):
        if not diff[3]:  # diff[3] is the 'corrected' status
            return i
    return 0  # If all are confirmed, start from the first

def setup_console(diffs, corrections):
    """Manage the console UI and save changes."""
    console = Console()
    progress = ProgressDisplay(len(diffs), console)

    # Start from the first unconfirmed difference
    index = find_first_unconfirmed(diffs)

    while True:
        key, o_text, p_text, corrected = diffs[index]
        progress.update_progress(index + 1, key, o_text, p_text, corrected)
        choice = console.input("[bold blue]Navigate with '.', ',' or 'q' to quit, 'e' to edit, 'enter' to save and move next, 'd' to delete, or 'n <number>' to jump:[/bold blue] ").strip().lower()

        if choice == 'q':
            break
        elif choice == ',':
            index = (index - 1) % len(diffs)
        elif choice == '.':
            index = (index + 1) % len(diffs)
        elif choice == 'e':
            edited_text = edit_text(p_text)
            diffs[index] = (key, o_text, edited_text, corrected)
        elif choice == '':
            corrections[key] = p_text
            console.print("[bold green]Value saved! Moving to next diff...[/bold green]")
            diffs[index] = (key, o_text, p_text, True)
            index = (index + 1) % len(diffs)
        elif choice.startswith('n '):
            try:
                new_index = int(choice.split()[1]) - 1
                if 0 <= new_index < len(diffs):
                    index = new_index
                else:
                    console.print(f"[bold red]Invalid number. Please enter a number between 1 and {len(diffs)}.[/bold red]")
            except ValueError:
                console.print("[bold red]Please enter a valid number after 'n '.[/bold red]")
        elif choice == 'd':
            if corrected:
                del corrections[key]  # Remove the correction
                diffs[index] = (key, o_text, p_text, False)  # Update the status in the UI
                console.print("[bold red]Correction deleted. Status updated.[/bold red]")
            else:
                console.print("[bold red]No confirmed correction to delete.[/bold red]")

    save_json(corrections, 'data/output-corrections.json')

def main():
    """Main function."""
    original_data = load_json('data/default.json')
    patched_data = load_json('data/output.json')
    
    # Check if corrections file exists and apply corrections
    corrections_file = 'data/output-corrections.json'
    corrections = {}
    if os.path.exists(corrections_file):
        corrections = load_json(corrections_file)
        patched_data = apply_corrections(patched_data, corrections)

    diffs = find_differences(original_data, patched_data, corrections)
    if not diffs:
        print("[bold red]No differences to display.[/bold red]")
        return
    setup_console(diffs, corrections)

if __name__ == "__main__":
    main()
