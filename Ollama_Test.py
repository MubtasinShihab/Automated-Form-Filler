import json
import ollama
import tkinter as tk
from tkinter import filedialog, simpledialog

# Initialize Tkinter and hide the root window.
root = tk.Tk()
root.withdraw()

# Open a file chooser dialog to let the user select a JSON file.
json_file_path = filedialog.askopenfilename(
    title="Select JSON file with persons",
    filetypes=[("JSON files", "*.json")]
)

# Load the JSON data.
with open(json_file_path, "r") as f:
    data = json.load(f)

# Retrieve the list of persons from the "profiles" key.
if "profiles" in data:
    persons = data["profiles"]
else:
    print("Error: JSON file does not contain 'profiles' key.")
    exit(1)

# List all available persons.
print("Available persons:")
for index, person in enumerate(persons, start=1):
    print(f"{index}. {person['name']}")

# Prompt the user with a GUI dialog for person selection.
choice = simpledialog.askstring("Input", "Which one are you? Enter the number:")

try:
    selected_index = int(choice) - 1
    selected_profile = persons[selected_index]  # store the entire profile dict
    selected_person = selected_profile["name"]
except (ValueError, IndexError):
    print("Invalid selection. Exiting.")
    exit(1)

# Build the initial question including the selected person's name.
model = "llama3.2:3b-instruct-q5_K_M"
initial_question = (
    f"You are a powerful API. The JSON file contains multiple persons. "
    f"Detected person: {selected_person}. "
    "Please confirm the selected person by returning a confirmation message."
)

# Call the ollama API with the initial question.
initial_response = ollama.chat(model=model, messages=[
    {
        'role': 'user',
        'content': initial_question,
    },
])

print("\nInitial Response from model:")
print(initial_response['message']['content'])

# Now, prompt the user to enter a label query.
label_query = simpledialog.askstring("Input", "Enter the label you want to search for:")

# Build a second query that includes the selected person's JSON data.
profile_json_str = json.dumps(selected_profile, indent=2)
second_question = (
    f"Based on the following JSON data for {selected_person}:\n{profile_json_str}\n\n"
    f"Please detect the field corresponding to the label '{label_query}' and return its value "
    f"in a clear and nicely formatted manner."
)

# Call the ollama API with the second question.
second_response = ollama.chat(model=model, messages=[
    {
        'role': 'user',
        'content': second_question,
    },
])

print("\nResponse for label query from model:")
print(second_response['message']['content'])