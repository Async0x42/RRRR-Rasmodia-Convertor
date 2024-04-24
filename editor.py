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

def save_corrections(corrections, corrections_hashes):
    """Save corrections and their hashes."""
    structured_corrections = {
        key: {
            'original_hash': corrections_hashes[key],
            'status': 'accepted' if corrections[key]['corrected'] else 'flagged for review',
            'corrected_text': corrections[key]['text']
        }
        for key in corrections
    }
    save_json(structured_corrections, 'data/output-corrections.json')

def apply_corrections(data, corrections):
    """Apply corrections on top of the original data."""
    corrected_data = data.copy()
    for key, correction in corrections.items():
        if correction['status'] in ['accepted', 'corrected']:
            corrected_data[key] = correction['corrected_text']
    return corrected_data

def find_differences(original, patched, corrections=None, corrections_hashes=None):
    """Compare two dictionaries and find differences."""
    diffs = []
    original_hashes = {key: hash_text(value) for key, value in original.items()}
    for key, value in patched.items():
        if original.get(key, None) != value:
            original_value = original.get(key, '')
            patched_value = value
            corrected = key in corrections
            hash_match = original_hashes[key] == corrections_hashes.get(key, '') if key in corrections_hashes else False
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

def setup_console(diffs, corrections, corrections_hashes):
    """Manage the console UI and save changes."""
    console = Console()
    progress = ProgressDisplay(len(diffs), console)

    # Start from the first unconfirmed difference
    index = find_first_unconfirmed(diffs)
    try:
        while True:
            # Ensure 'hash_match' is correctly evaluated
            if len(diffs[index]) == 4:
                key, o_text, p_text, corrected = diffs[index]
                hash_match = hash_text(o_text) == corrections_hashes.get(key, '')
                diffs[index] = (key, o_text, p_text, corrected, hash_match)
            
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
                # Update diffs and preserve all fields including hash_match
                diffs[index] = (key, o_text, edited_text, corrected, hash_match)
            elif choice == '':
                corrections[key] = {'text': p_text, 'corrected': True}
                # Recalculate and update hash in corrections_hashes to reflect the new original text
                new_hash = hash_text(o_text)
                corrections_hashes[key] = new_hash
                console.print("[bold green]Value saved and hash updated! Moving to next diff...[/bold green]")
                diffs[index] = (key, o_text, p_text, True, True)  # Set corrected to True and hash_match to True
                index = (index + 1) % len(diffs)
            elif choice.startswith('n '):
                new_index = int(choice.split()[1]) - 1
                if 0 <= new_index < len(diffs):
                    index = new_index
                else:
                    console.print(f"[bold red]Invalid number. Please enter a number between 1 and {len(diffs)}.[/bold red]")
            elif choice == 'd':
                if corrected:
                    del corrections[key]
                    del corrections_hashes[key]  # Also delete the hash from hashes dictionary
                    diffs[index] = (key, o_text, p_text, False, False)
                    console.print("[bold red]Correction and hash deleted. Status updated.[/bold red]")
                else:
                    console.print("[bold red]No confirmed correction to delete.[/bold red]")

        save_corrections(corrections, corrections_hashes)
    except KeyboardInterrupt:
        user_input = console.input("\nDo you want to [bold red]'save and quit'[/bold red] or [bold red]'quit without saving'[/bold red]? (Type 'save' to save): ").strip().lower()
        if user_input == 'save':
            save_corrections(corrections, corrections_hashes)
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
    setup_console(diffs, corrections, corrections_hashes)

if __name__ == "__main__":
    main()
