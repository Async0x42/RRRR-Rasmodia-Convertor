# path/filename: update_display_script.py
import json5
from rich.console import Console
from rich.text import Text
import sys

# Step 1: Load JSON data from a file
def load_json(filename):
    with open(filename, 'r') as file:
        return json5.load(file)

# Step 2: Compare two dictionaries and find differences
def find_differences(original, patched):
    diffs = []
    for key in patched:
        original_value = original.get(key, '')
        patched_value = patched[key]
        original_text = f"{key}: {original_value}"
        patched_text = f"{key}: {patched_value}"
        diffs.append((original_text, patched_text))
    return diffs

# Step 3: Highlight differing words and display them
def setup_console(diffs):
    console = Console()
    index = 0

    def show_diff():
        console.clear()
        o_text, p_text = diffs[index]
        console.print(highlight_differences(o_text, p_text))

    def highlight_differences(original, patched):
        # Split on the first colon to separate keys from values
        original_key, original_rest = original.split(':', 1)
        patched_key, patched_rest = patched.split(':', 1)

        highlighted_text = Text()
        # Style the key
        highlighted_text.append(original_key + ':', style="bold blue")
        # Compare the rest (values)
        original_words = original_rest.strip().split()
        patched_words = patched_rest.strip().split()
        for o_word, p_word in zip(original_words, patched_words):
            if o_word != p_word:
                highlighted_text.append(' ').append(o_word, style="red strike")
                highlighted_text.append(' ' + p_word, style="green")
            else:
                highlighted_text.append(' ' + o_word, style="default")
        return highlighted_text

    show_diff()
    while True:
        key = console.input("[bold blue]Navigate with '.', ',' or 'q' to quit: [/bold blue]").strip().lower()
        if key == 'q':
            break
        elif key == '.' and index < len(diffs) - 1:
            index += 1
            show_diff()
        elif key == ',' and index > 0:
            index -= 1
            show_diff()

# Main function to load data and show differences
def main():
    original_data = load_json('data/default.json')
    patched_data = load_json('data/output.json')
    diffs = find_differences(original_data, patched_data)
    setup_console(diffs)

if __name__ == "__main__":
    main()
