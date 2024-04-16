# /path/to/your_script.py

import re
import json

# Gender mapping with basic forms
# TODO: Magnus
gender_map = {
    r'\bhe\b': 'she', r'\bhis\b': 'her', r'\bhim\b': 'her', r'\bhimself\b': 'herself',
    r'\bman\b': 'woman', r'\bboy\b': 'girl', r'\bbrother\b': 'sister',
    r'\bfather\b': 'mother', r'\bson\b': 'daughter', r'\bhusband\b': 'wife', r'\bdad\b': 'mom',
    r'\bmr.\b': 'mrs.', r'\bwizard\b': 'witch', r'\brasmodius\b': 'rasmodia'
}

def apply_case(word, example):
    """Applies the case of 'example' to 'word', assuming both are single words."""
    if example.islower():
        return word.lower()
    elif example.isupper():
        return word.upper()
    elif example.istitle():
        return word.title()
    return word

def gender_swap(text):
    def replace(match):
        word = match.group(0)
        for male, female in gender_map.items():
            if re.fullmatch(male, word, re.IGNORECASE):
                return apply_case(female, word)
        return word  # No change if no match is found

    pattern = r'\b(?:' + '|'.join(gender_map.keys()) + r')\b'
    return re.sub(pattern, replace, text, flags=re.IGNORECASE)

def clean_json(json_str):
    """Remove single-line comments and unescape problematic control characters from JSON strings."""
    # Remove single-line comments
    no_comments = re.sub(r"//.*", "", json_str)
    # Unescape control characters
    return re.sub(r"[\n\r\t]+", "", no_comments)

def load_json_file(filename):
    """Read and clean the JSON file, then convert to Python dictionary."""
    try:
        with open(filename, 'r') as file:
            clean_content = clean_json(file.read())
        return json.loads(clean_content)
    except json.JSONDecodeError as e:
        raise ValueError(f"Error parsing JSON: {str(e)}")

def write_json_file(filename, data):
    with open(filename, 'w') as file:
        json.dump(data, file, indent=4)
        
def swap_all_genders(json_data):
    output_data = {}
    for key, value in json_data.items():
        swapped_text = gender_swap(value)
        if swapped_text != value:
            output_data[key] = swapped_text
            print(f"Difference found for '{key}': {swapped_text}")

    if output_data:
        write_json_file("data/output.json", output_data)

try:
    json_data = load_json_file("data/test.json")
    swap_all_genders(json_data)
except Exception as e:
    print(e)
