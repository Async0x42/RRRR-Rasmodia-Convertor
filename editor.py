import json
import json5
from rich.console import Console
from rich.table import Table
from rich.text import Text
from prompt_toolkit import PromptSession
import hashlib
import os

def load_json(filename):
    """Load JSON data from a file."""
    try:
        with open(filename, 'r') as file:
            return json5.load(file)
    except FileNotFoundError:
        return {}  # Return empty dict if file not found

def save_json(data, filename):
    """Save JSON data to a file securely."""
    temp_filename = filename + '.tmp'
    with open(temp_filename, 'w') as file:
        json.dump(data, file, indent=4)
    os.replace(temp_filename, filename)

def hash_text(text):
    """Create a hash for the given text."""
    return hashlib.sha256(text.encode()).hexdigest()

def save_corrections(corrections):
        save_json(corrections, 'data/output-corrections.json')
        save_json(corrections_hashes, 'data/output-corrections-hashes.json')

def apply_corrections(data, corrections):
    """Apply corrections on top of the original data."""
    corrected_data = data.copy()
    corrected_data.update(corrections)
    return corrected_data

def find_differences(original, patched, corrections=None, corrections_hashes=None):
    """Compare two dictionaries and find differences."""
    diffs = []
    original_hashes = {}
    for key in patched:
        if original.get(key, None) != patched[key]:
            original_value = original.get(key, '')
            patched_value = patched[key]
            corrected = key in corrections if corrections else False
            
            # Check if the hash exists in the corrections_hashes to avoid KeyError
            if corrections_hashes and key in corrections_hashes:
                hash_match = hash_text(original_value) == corrections_hashes[key]
            else:
                hash_match = False  # Default to False if no hash is found
            
            diffs.append((key, original_value, patched_value, corrected, hash_match))
    return diffs

class ProgressDisplay:
    """Display progress of operations in a table format."""
    def __init__(self, total, console):
        self.total = total
        self.current = 0
        self.console = console
        self.table = Table()

    def update_progress(self, current, key, o_text, p_text, corrected, hash_match):
        """Update the progress displayed on the console."""
        self.current = current
        self.console.clear()
        self.table.columns = []
        self.table.add_column("Key", justify="right")
        self.table.add_column("Text", justify="left")
        self.table.rows = []
        self.table.add_row(highlight_key(key), highlight_differences(o_text, p_text))
        self.table.add_row("[bold blue]Diff Progress:[/bold blue]", f"[dark_blue]{self.current}/{self.total}[/dark_blue]")
        status_text = "[bold green]ACCEPTED/CORRECTED[/bold green]" if corrected else "[bold red]UNCONFIRMED[/bold red]"
        self.table.add_row("[bold]Status:[/bold]", status_text)
        hash_status = "[bold green]HASH MATCH[/bold green]" if hash_match else "[bold red]HASH MISMATCH[/bold red]"
        self.table.add_row("[bold]Hash Status:[/bold]", hash_status)
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
    try:
        while True:
            key, o_text, p_text, corrected, hash_match = diffs[index]
            progress.update_progress(index + 1, key, o_text, p_text, corrected, hash_match)
            console.print("[blue]Navigate with [bold]'.'[/bold], [bold]','[/bold] or [bold]'n <number>'[/bold] to jump[/blue]")
            console.print("[blue][bold]'d'[/bold] to delete, [bold]'e'[/bold] to edit, [bold]'enter'[/bold] to accept and move next, or [bold]'q'[/bold] to save and quit[/blue]")
            choice = console.input("Command: ").strip().lower()

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
                    
        save_corrections(corrections);
    except KeyboardInterrupt:
        user_input = console.input("\nDo you want to [bold red]'save and quit'[/bold red] or [bold red]'quit without saving'[/bold red]? (Type 'save' to save): ").strip().lower()
        if user_input == 'save':
            save_corrections(corrections)
        console.print("[bold red]Exiting now![/bold red]")

def main():
    """Main function."""
    original_data = load_json('data/default.json')
    patched_data = load_json('data/output.json')
    
    # Load corrections and apply them
    corrections = load_json('data/output-corrections.json')
    patched_data = apply_corrections(patched_data, corrections)

    # Load correction hashes
    corrections_hashes = load_json('data/output-corrections-hashes.json')
        
    diffs = find_differences(original_data, patched_data, corrections, corrections_hashes)

    if not diffs:
        print("[bold red]No differences to display.[/bold red]")
        return
    setup_console(diffs, corrections)

if __name__ == "__main__":
    main()
