import json
import json5
from rich.console import Console
from rich.table import Table
from rich.text import Text
from prompt_toolkit import PromptSession
import hashlib
import os
import datetime

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

def save_patch(corrections):
    """Save only the corrected text for each key to patch.json, skipping 'skipped' entries."""
    patch_data = {
        key: correction['corrected_text'] for key, correction in corrections.items()
        if correction['corrected_text'] and correction.get('status') != 'skipped'
    }
    save_json(patch_data, 'data/patch.json')
    
def hash_text(text):
    """Create a hash for the given text."""
    return hashlib.sha256(text.encode()).hexdigest()

def save_corrections(corrections):
    """Save corrections and their hashes."""
    structured_corrections = {
        key: {
            'original_hash': corrections[key]['original_hash'],
            'status': corrections[key]['status'],
            'corrected_text': corrections[key]['corrected_text'],
            'last_updated': corrections[key]['last_updated']
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

def find_differences(original, patched, corrections=None):
    """Compare two dictionaries and find differences."""
    diffs = []
    original_hashes = {key: hash_text(value) for key, value in original.items()}
    for key, value in patched.items():
        if original.get(key, None) != value:
            original_value = original.get(key, '')
            patched_value = value
            corrected = key in corrections
            hash_match = original_hashes[key] == corrections[key]['original_hash'] if key in corrections else False
            diffs.append((key, original_value, patched_value, corrected, hash_match))
    return diffs

class ProgressDisplay:
    """Display progress of operations in a table format."""
    def __init__(self, total, console):
        self.total = total
        self.current = 0
        self.console = console
        self.table = Table()

    def update_progress(self, current, key, o_text, p_text, corrected, hash_match, corrections):
        """Update the progress displayed on the console."""
        self.current = current
        self.console.clear()
        self.table.columns = []
        self.table.add_column("Key", justify="right")
        self.table.add_column("Text", justify="left")
        self.table.rows = []
        self.table.add_row(highlight_key(key), highlight_differences(o_text, p_text))
        
        # Determine the status text based on the current status in corrections
        status = corrections.get(key, {}).get('status', 'unconfirmed')  # Default to 'unconfirmed' if not found
        if status == 'accepted':
            status_text = "[bold green]ACCEPTED/CORRECTED[/bold green]"
        elif status == 'to_review':
            status_text = "[bold yellow]FLAGGED FOR REVIEW[/bold yellow]"
        elif status == 'skipped':
            status_text = "[bold green]SKIPPED[/bold green]"
        else:
            status_text = "[bold red]UNCONFIRMED[/bold red]"
        self.table.add_row("[bold]Status:[/bold]", status_text)
    
        hash_status = "[bold green]HASH MATCH[/bold green]" if hash_match else "[bold red]HASH MISMATCH[/bold red]"
        self.table.add_row("[bold]Hash Status:[/bold]", hash_status)
        last_updated = corrections.get(key, {}).get('last_updated', 'n/a')  # Safe access with default 'n/a'
        self.table.add_row("[bold]Last Updated:[/bold]", last_updated)
        self.table.add_row()
        self.table.add_row("[bold blue]Diff Progress:[/bold blue]", f"[dark_blue]{self.current}/{self.total}[/dark_blue]")
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
    """Prepopulate and allow editing of text with cursor control and mouse support."""
    session = PromptSession()
    def pre_run():
        session.app.current_buffer.cursor_position = text.find('[') if '[' in text else 0
    return session.prompt("[bold blue]Edit text:[/bold blue] ", default=text, pre_run=pre_run, mouse_support=True)

def find_first_unconfirmed(diffs, corrections):
    """Find the index of the first unconfirmed or flagged for review difference."""
    for i, (key, o_text, p_text, corrected, hash_match) in enumerate(diffs):
        status = corrections.get(key, {}).get('status', 'unconfirmed')  # Default to 'unconfirmed' if not found
        if status in ['unconfirmed', 'to_review']:
            return i
    return -1  # Return -1 if no unconfirmed or to_review diffs found

def find_next_actionable_index(diffs, corrections, current_index):
    """Find the next index with unconfirmed or flagged for review status, or hash mismatch."""
    # Start searching from the next index
    start_index = current_index + 1
    num_diffs = len(diffs)
    for i in range(start_index, start_index + num_diffs):  # Wrap around if needed
        idx = i % num_diffs
        key, o_text, p_text, corrected, hash_match = diffs[idx]
        status = corrections.get(key, {}).get('status', 'unconfirmed')
        if status in ['unconfirmed', 'to_review'] or not hash_match:
            return idx
    return -1  # Return -1 if no actionable diff found

def setup_console(diffs, corrections):
    """Manage the console UI and save changes."""
    console = Console()
    progress = ProgressDisplay(len(diffs), console)

    index = find_first_unconfirmed(diffs, corrections)
    if index == -1:  # Handle case where no unconfirmed or flagged diffs are found
        console.print("[bold red]No unconfirmed or flagged differences to display. Starting from 0.[/bold red]")
        index = 0
    
    try:
        while True:
            key, o_text, p_text, corrected, hash_match = diffs[index]
            progress.update_progress(index + 1, key, o_text, p_text, corrected, hash_match, corrections)
            console.print("[blue]Navigate with [bold]'.'[/bold], [bold]','[/bold], [bold]'ff'[/bold] to fast forward past confirmed or skipped, or [bold]'n <number>'[/bold] to jump[/blue]")
            console.print("[blue][bold]'d'[/bold] to delete, [bold]'e'[/bold] to edit, [bold]'s'[/bold] to save all, [bold]'k'[/bold] to toggle skipping, [bold]'f'[/bold] to flag for review, [bold]'enter'[/bold] to accept and move next, or [bold]'q'[/bold] to save and quit[/blue]")
            choice = console.input("Command: ").strip().lower()

            if choice == 'q':
                break
            elif choice == ',':
                index = (index - 1) % len(diffs)
            elif choice == '.':
                index = (index + 1) % len(diffs)
            elif choice == 'e':
                edited_text = edit_text(p_text)
                diffs[index] = (key, o_text, edited_text, corrected, hash_match)
            elif choice == 's':
                save_patch(corrections)
                save_corrections(corrections)
                console.print("[bold green]All corrections saved to patch.json![/bold green]")
            elif choice == 'f':
                if key in corrections:
                    # Update only the status if the key already exists
                    corrections[key]['status'] = 'to_review'
                else:
                    # Create a new entry if the key does not exist
                    corrections[key] = {
                        'original_hash': hash_text(o_text),
                        'corrected_text': p_text,
                        'status': 'to_review',
                        'last_updated': datetime.datetime.now().isoformat()
                    }
                    diffs[index] = (key, o_text, p_text, False, True)
                console.print(f"[bold yellow]Flagged '{key}' for review.[/bold yellow]")
            elif choice == 'ff':  # Fast-forward command
                next_index = find_next_actionable_index(diffs, corrections, index)
                if next_index != -1:
                    index = next_index
                else:
                    console.print("[bold red]No more items to fast-forward to.[/bold red]")
            elif choice == 'k':  # Assume 'k' is the chosen key for toggling skip
                if key in corrections:
                    if corrections[key].get('status') == 'skipped':
                        corrections[key]['status'] = 'unconfirmed'  # Toggle off skip
                    else:
                        corrections[key]['status'] = 'skipped'  # Toggle on skip
                else:
                    corrections[key] = {
                        'original_hash': hash_text(o_text),
                        'corrected_text': p_text,
                        'status': 'skipped',
                        'last_updated': datetime.datetime.now().isoformat()
                    }
                console.print(f"[bold yellow]Toggled '{key}' skipped status.[/bold yellow]")
            elif choice == '':
                new_hash = hash_text(o_text)
                corrections[key] = {'original_hash': new_hash, 'corrected_text': p_text, 'status': 'accepted', 'last_updated': datetime.datetime.now().isoformat()}
                diffs[index] = (key, o_text, p_text, True, True)
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
                    diffs[index] = (key, o_text, p_text, False, False)
                    console.print("[bold red]Correction and hash deleted. Status updated.[/bold red]")
                else:
                    console.print("[bold red]No confirmed correction to delete.[/bold red]")

        save_corrections(corrections)
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
        
    diffs = find_differences(original_data, patched_data, corrections)

    if not diffs:
        print("[bold red]No differences to display.[/bold red]")
        return
    setup_console(diffs, corrections)

if __name__ == "__main__":
    main()
