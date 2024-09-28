import os
import gzip
import argparse
import pandas as pd

def get_file_size(file_path):
    """Returns the size of a file in bytes."""
    return os.path.getsize(file_path)

def compress_file(file_path, output_file):
    """Compresses a file using gzip and writes it to the output_file."""
    with open(file_path, 'rb') as f_in, gzip.open(output_file, 'wb') as f_out:
        f_out.writelines(f_in)

def delete_file(file_path):
    """Deletes a file from the filesystem."""
    if os.path.exists(file_path):
        os.remove(file_path)
        print(f"Deleted: {file_path}")
    else:
        print(f"File not found for deletion: {file_path}")

def generate_input_files(style):
    """Generates two files based on 'p_norm_{style}.tsv' found in 'output_files'."""
    # Use the style to determine the base directory
    base_directory = os.path.join(os.getcwd(), style)
    
    # Define the path to the 'p_norm_{style}.tsv' file
    p_norm_file = os.path.join(base_directory, 'output_files', f'p_norm_{style}.tsv')

    # Ensure the p_norm file exists
    if not os.path.exists(p_norm_file):
        print(f"Error: File {p_norm_file} not found.")
        return None, None

    # Load the p_norm file using pandas
    df = pd.read_csv(p_norm_file, sep='\t')

    # Define column name for the first file in 'input_files'
    column_name_input = 'location' if style == 'data_loc' else 'h_age' if style == 'age' else 'unknown'

    # Ensure the column exists in the dataframe
    if column_name_input not in df.columns:
        print(f"Error: Column '{column_name_input}' not found in {p_norm_file}.")
        return None, None

    # Generate the 'pre_norm_{style}.tsv' file in 'input_files'
    pre_norm_file = os.path.join(base_directory, 'input_files', f'pre_norm_{style}.tsv')
    df[[column_name_input]].to_csv(pre_norm_file, sep='\t', index=False)

    # Define column name for the second file in 'output_files'
    column_name_output = 'split_word_normalized_location' if style == 'data_loc' else 'word_normalized_h_age' if style == 'age' else 'unknown'

    # Ensure the column exists in the dataframe
    if column_name_output not in df.columns:
        print(f"Error: Column '{column_name_output}' not found in {p_norm_file}.")
        return None, None

    # Generate the second file in 'output_files'
    output_file = os.path.join(base_directory, 'output_files', f'post_norm_{style}.tsv')
    df[[column_name_output]].to_csv(output_file, sep='\t', index=False)

    return pre_norm_file, output_file

def format_number(value, size_units):
    """Formats numbers with commas, and no decimals for bytes, but with two decimals for MB."""
    if size_units == 'mb':
        return f"{value:,.2f}"  # Two decimal places for MB
    else:
        return f"{int(value):,}"  # No decimal places for bytes

def calculate_percentage_difference(value1, value2):
    """Calculates the percentage difference between two values."""
    return ((value1 - value2) / value1) * 100

def display_sizes(raw_size, compressed_size, size_units):
    """Displays raw and compressed sizes in the specified units."""
    if size_units == 'mb':
        raw_size_display = bytes_to_mb(raw_size)
        compressed_size_display = bytes_to_mb(compressed_size)
    else:
        raw_size_display = raw_size
        compressed_size_display = compressed_size
    
    return format_number(raw_size_display, size_units), format_number(compressed_size_display, size_units)

def bytes_to_mb(size_in_bytes):
    """Converts bytes to megabytes."""
    return size_in_bytes / (1024 * 1024)

def main(style, size_units):
    # Use the style to determine the base directory
    base_directory = os.path.join(os.getcwd(), style)

    # Generate the two files in 'input_files' and 'output_files'
    pre_norm_file, output_file = generate_input_files(style)

    if not pre_norm_file or not output_file:
        print("Error: Could not generate the necessary files.")
        return

    # Get raw file sizes
    size_input_raw = get_file_size(pre_norm_file)
    size_output_raw = get_file_size(output_file)

    # Compress the files and save them as .gz
    compressed_input_file = pre_norm_file + '.gz'
    compressed_output_file = output_file + '.gz'
    compress_file(pre_norm_file, compressed_input_file)
    compress_file(output_file, compressed_output_file)

    # Get compressed file sizes
    size_input_compressed = get_file_size(compressed_input_file)
    size_output_compressed = get_file_size(compressed_output_file)

    # Display file sizes based on the unit specified
    raw_size_input_display, compressed_size_input_display = display_sizes(size_input_raw, size_input_compressed, size_units)
    raw_size_output_display, compressed_size_output_display = display_sizes(size_output_raw, size_output_compressed, size_units)

    # Print results for input file
    print(f"Input File: {pre_norm_file}")
    print(f"  Raw size: {raw_size_input_display} {'MB' if size_units == 'mb' else 'bytes'}")
    print(f"  Compressed size: {compressed_size_input_display} {'MB' if size_units == 'mb' else 'bytes'}")
    print(f"  Difference (raw vs compressed): {format_number(abs(size_input_raw - size_input_compressed) if size_units == 'b' else abs(bytes_to_mb(size_input_raw) - bytes_to_mb(size_input_compressed)), size_units)} {'MB' if size_units == 'mb' else 'bytes'}")
    print(f"  Compression saved: {format_number(calculate_percentage_difference(size_input_raw, size_input_compressed), 'mb')}%")
    
    # Print results for output file
    print(f"Output File: {output_file}")
    print(f"  Raw size: {raw_size_output_display} {'MB' if size_units == 'mb' else 'bytes'}")
    print(f"  Compressed size: {compressed_size_output_display} {'MB' if size_units == 'mb' else 'bytes'}")
    print(f"  Difference (raw vs compressed): {format_number(abs(size_output_raw - size_output_compressed) if size_units == 'b' else abs(bytes_to_mb(size_output_raw) - bytes_to_mb(size_output_compressed)), size_units)} {'MB' if size_units == 'mb' else 'bytes'}")
    print(f"  Compression saved: {format_number(calculate_percentage_difference(size_output_raw, size_output_compressed), 'mb')}%")
    
    # Difference between raw file sizes and compressed file sizes
    raw_difference = abs(size_input_raw - size_output_raw)
    compressed_difference = abs(size_input_compressed - size_output_compressed)
    
    raw_difference_display = format_number(bytes_to_mb(raw_difference) if size_units == 'mb' else raw_difference, size_units)
    compressed_difference_display = format_number(bytes_to_mb(compressed_difference) if size_units == 'mb' else compressed_difference, size_units)
    
    print("\nDifferences between the input and output files:")
    print(f"  Difference in raw sizes: {raw_difference_display} {'MB' if size_units == 'mb' else 'bytes'}")
    print(f"  Percentage difference (output vs input): {format_number(calculate_percentage_difference(size_input_raw, size_output_raw), 'mb')}%")
    print(f"  Difference in compressed sizes: {compressed_difference_display} {'MB' if size_units == 'mb' else 'bytes'}")
    print(f"  Percentage difference (output compressed vs input compressed): {format_number(calculate_percentage_difference(size_input_compressed, size_output_compressed), 'mb')}%")

    # Delete the compressed .gz files after checking their sizes
    delete_file(compressed_input_file)
    delete_file(compressed_output_file)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Compress two TSV files and report file sizes.')
    parser.add_argument('style', type=str, help='The style parameter for file naming (e.g., data_loc or age)')
    parser.add_argument('--size_units', type=str, choices=['b', 'mb'], default='b', help='Display sizes in bytes (b) or megabytes (mb)')

    args = parser.parse_args()
    main(args.style, args.size_units)
