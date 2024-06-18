# RRRR-Rasmodia-Convertor

# Text Editor for Corrections

This Python script, `editor.py`, is designed to facilitate the review and correction of text data. It allows users to navigate through text differences, accept corrections, edit text, and flag items for review.

## Features

- Load and compare text data from JSON files.
- Navigate through text differences with commands.
- Edit, accept, and flag text corrections.
- Save corrections in JSON format.

## Prerequisites

Before you can run this script, make sure you have Python installed on your machine. This script has been tested with Python 3.11 and above.

## Setting Up Your Environment

To run this script, you'll need to set up a Python virtual environment and install the necessary packages. Follow these steps to get started:

### Step 1: Clone the Repository

Clone this repository to your local machine using the following command:

```bash
git clone [URL to the repository]
cd [repository name]
```

Step 2: Create a Virtual Environment
Run the following command in the root of your repository to create a virtual environment:

```bash
python -m venv venv
```
Step 3: Activate the Virtual Environment
Activate the virtual environment by running:

Windows:
```bash
.\venv\Scripts\activate
```

macOS/Linux:
```bash
source venv/bin/activate
```

Step 4: Install Dependencies
Install the required packages using pip:

```bash
pip install -r requirements.txt
```

Running the Script
Once you have set up everything, you can run the script using:

```bash
python app.py
```
This will convert strings matching replacements.txt from the RRRR default.json and output it to output.json

```bash
python editor.py
```
This will launch the editor using both default.json and output.json, saving any user edits to output-corrections.json. When the user saves all changes, a patch.json is made with only the changed strings. output-corrections.json contains the status of corrections and hash info to detect if any source lines (default.json) changed since the last time there was a correction.

Navigating the Script
- Use . and , to navigate forward and backward through differences.
- Use n <number> to jump to a specific difference.
- Press d to delete a correction.
- Press e to edit the selected text.
- Press s to save all changes to the corrections.
- Press f to flag a text for review.
- Press k to toggle the skip status.
- Press enter to accept a correction and move to the next.
- Press q to quit the program, with an option to save changes.
- Press ff to fast-forward to the next unconfirmed or flagged item.

Ensure your JSON data files are correctly placed under the data directory as specified in the script for it to function properly.
