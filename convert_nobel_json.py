import json

input_file_path = "/Users/anhdao/Aalto/Fall 2025/cs-e4780-scalable-systems/ScalableSys-Proj2/data/nobel.json"
output_file_path = "/Users/anhdao/Aalto/Fall 2025/cs-e4780-scalable-systems/ScalableSys-Proj2/data/nobel_utf8.json"

try:
    with open(input_file_path, 'r', encoding='utf-8') as infile:
        data = json.load(infile)

    with open(output_file_path, 'w', encoding='utf-8') as outfile:
        json.dump(data, outfile, indent=2, ensure_ascii=False)

    print(f"Successfully converted '{input_file_path}' to '{output_file_path}' with UTF-8 encoding.")
except FileNotFoundError:
    print(f"Error: The file '{input_file_path}' was not found.")
except json.JSONDecodeError:
    print(f"Error: Could not decode JSON from '{input_file_path}'. Check file format.")
except Exception as e:
    print(f"An unexpected error occurred: {e}")
