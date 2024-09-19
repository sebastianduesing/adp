import os
import gzip
import argparse

def get_file_size(file_path):
    """Returns the size of a file in bytes."""
    return os.path.getsize(file_path)

def compress_file(file_path, output_file):
    """Compresses a file using gzip and writes it to the output_file."""
    with open(file_path, 'rb') as f_in, gzip.open(output_file, 'wb') as f_out:
        f_out.writelines(f_in)

def find_minimal_file(directory):
    """Finds a file starting with 'minimal_' and ending with '.tsv' in the given directory."""
    files = [os.path.join(directory, f) for f in os.listdir(directory) if f.startswith('minimal_') and f.endswith('.tsv')]
    
    if len(files) != 1:
        print(f"Error: Expected exactly 1 file starting with 'minimal_' in {directory}, found {len(files)}")
        return None
    
    return files[0]

def bytes_to_mb(size_in_bytes):
    """Converts bytes to megabytes."""
    return size_in_bytes / (1024 * 1024)

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

def main(base_directory, size_units):
    # Define input and output directories
    input_dir = os.path.join(base_directory, 'input_files')
    output_dir = os.path.join(base_directory, 'output_files')

    # Find the 'minimal_' file in both input and output directories
    input_file = find_minimal_file(input_dir)
    output_file = find_minimal_file(output_dir)

    if input_file is None or output_file is None:
        return

    # Get raw file sizes
    size_input_raw = get_file_size(input_file)
    size_output_raw = get_file_size(output_file)

    # Compress the files and save them as .gz
    compressed_input_file = input_file + '.gz'
    compressed_output_file = output_file + '.gz'
    compress_file(input_file, compressed_input_file)
    compress_file(output_file, compressed_output_file)

    # Get compressed file sizes
    size_input_compressed = get_file_size(compressed_input_file)
    size_output_compressed = get_file_size(compressed_output_file)

    # Display file sizes based on the unit specified
    raw_size_input_display, compressed_size_input_display = display_sizes(size_input_raw, size_input_compressed, size_units)
    raw_size_output_display, compressed_size_output_display = display_sizes(size_output_raw, size_output_compressed, size_units)

    # Print results for input file
    print(f"Input File: {input_file}")
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

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Compress two TSV files and report file sizes.')
    parser.add_argument('base_directory', type=str, help='Base directory containing the input_files and output_files subdirectories')
    parser.add_argument('--size_units', type=str, choices=['b', 'mb'], default='b', help='Display sizes in bytes (b) or megabytes (mb)')

    args = parser.parse_args()
    main(args.base_directory, args.size_units)
