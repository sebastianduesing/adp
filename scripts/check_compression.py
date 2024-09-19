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
    b_in_MB = 1000000
    return size_in_bytes / b_in_MB

def calculate_percentage_difference(value1, value2):
    """Calculates the percentage difference between two values."""
    return ((value1 - value2) / value1) * 100

def main(base_directory):
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

    # Convert file sizes to MB
    size_input_raw_mb = bytes_to_mb(size_input_raw)
    size_output_raw_mb = bytes_to_mb(size_output_raw)
    size_input_compressed_mb = bytes_to_mb(size_input_compressed)
    size_output_compressed_mb = bytes_to_mb(size_output_compressed)

    # Print results
    print(f"Input File: {input_file}")
    print(f"  Raw size: {size_input_raw_mb:.2f} MB")
    print(f"  Compressed size: {size_input_compressed_mb:.2f} MB")
    print(f"  Difference (raw vs compressed): {size_input_raw_mb - size_input_compressed_mb:.2f} MB")
    print(f"  Compression saved: {calculate_percentage_difference(size_input_raw, size_input_compressed):.2f}%")
    
    print(f"Output File: {output_file}")
    print(f"  Raw size: {size_output_raw_mb:.2f} MB")
    print(f"  Compressed size: {size_output_compressed_mb:.2f} MB")
    print(f"  Difference (raw vs compressed): {size_output_raw_mb - size_output_compressed_mb:.2f} MB")
    print(f"  Compression saved: {calculate_percentage_difference(size_output_raw, size_output_compressed):.2f}%")
    
    # Difference between raw file sizes
    raw_difference_mb = size_input_raw_mb - size_output_raw_mb
    compressed_difference_mb = size_input_compressed_mb - size_output_compressed_mb

    print("\nDifferences between the input and output files:")
    print(f"  Difference in raw sizes: {raw_difference_mb:.2f} MB")
    print(f"  Percentage difference (output vs input): {calculate_percentage_difference(size_input_raw, size_output_raw):.2f}%")
    
    print(f"  Difference in compressed sizes: {compressed_difference_mb:.2f} MB")
    print(f"  Percentage difference (output compressed vs input compressed): {calculate_percentage_difference(size_input_compressed, size_output_compressed):.2f}%")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Compress two TSV files and report file sizes.')
    parser.add_argument('base_directory', type=str, help='Base directory containing the input_files and output_files subdirectories')

    args = parser.parse_args()
    main(args.base_directory)
