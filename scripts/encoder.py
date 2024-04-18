import sys
import os
import chardet

def detect_file_encoding(file_path):
    """Detect the character encoding of the given file."""
    with open(file_path, 'rb') as f:
        result = chardet.detect(f.read())
    return result['encoding']


def convert_file_encoding(input_file_path, original_encoding, target_encoding):
    """Convert file from one encoding to another."""
    # Construct new file path
    new_file_path = f"{os.path.splitext(input_file_path)[0]}_{target_encoding}{os.path.splitext(input_file_path)[1]}"

    # Read in original encoding and write in target encoding
    with open(input_file_path, 'r', encoding=original_encoding) as infile, \
            open(new_file_path, 'w', encoding=target_encoding) as outfile:
        content = infile.read()
        outfile.write(content)
    return new_file_path


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python script.py <file_path> <target_encoding>")
        sys.exit(1)

    file_path = sys.argv[1]
    target_encoding = sys.argv[2]

    # Detect the current encoding of the file
    current_encoding = detect_file_encoding(file_path)
    print(f"The encoding of the file is: {current_encoding}")

    # Check if the current encoding is different from the target encoding
    if current_encoding.lower() == target_encoding.lower():
        print(f"The file is already in {target_encoding} encoding.")
    else:
        new_file_path = convert_file_encoding(file_path, current_encoding, target_encoding)
        print(f"File converted and saved to {new_file_path}.")
