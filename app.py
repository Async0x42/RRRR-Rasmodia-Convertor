import re
import csv
import json
import json5

def load_replacements(filename, delimiter='|'):
    """Loads gender mappings from a txt file with a custom delimiter."""
    with open(filename, newline='', encoding='utf-8') as file:
        reader = csv.reader(file, delimiter=delimiter)
        return {row[0]: row[1] for row in reader if row}

replacement_map = load_replacements('replacements.txt', delimiter='|')

def apply_case(word, example):
    """Applies the case of 'example' to 'word', assuming both are single words."""
    if example.islower():
        return word.lower()
    elif example.isupper():
        return word.upper()
    elif example.istitle():
        return word.title()
    return word

def replacement_swap(text):
    """Replaces specific words in the text with their counterparts using regex matching."""
    def replace(match):
        word = match.group(0)
        for male, female in replacement_map.items():
            if re.fullmatch(male, word, re.IGNORECASE):
                return apply_case(female, word)
        return word  # No change if no match is found

    pattern = r'\b(?:' + '|'.join(replacement_map.keys()) + r')\b'
    return re.sub(pattern, replace, text, flags=re.IGNORECASE)

def load_json_file(filename):
    """Read and clean the JSON file, then convert to Python dictionary using json5."""
    with open(filename, 'r') as file:
        return json5.loads(file.read())

def write_json_file(filename, data):
    """Write data to a JSON file using json5 for better format handling."""
    with open(filename, 'w') as file:
        json.dump(data, file, indent=4)
        
def swap_all_replacements(json_data):
    """Swap all gender-specific words found in the JSON data."""
    output_data = {}
    for key, value in json_data.items():
        swapped_text = replacement_swap(value)
        if swapped_text != value:
            output_data[key] = swapped_text
            print(f"Difference found for '{key}': {swapped_text}")

    if output_data:
        write_json_file("data/output.json", output_data)

try:
    json_data = load_json_file("data/default.json")
    swap_all_replacements(json_data)
except Exception as e:
    print(e)
