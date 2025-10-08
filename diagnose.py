import sys
import struct

def diagnose_file(file_path):
    """
    Safely reads the first 32 bytes of a file and prints its header data.
    This script is designed to be extremely simple to avoid crashing.
    """
    try:
        with open(file_path, "rb") as f:
            header_bytes = f.read(32)
    except FileNotFoundError:
        print(f"Error: The file '{file_path}' was not found.")
        sys.exit(1)
    except Exception as e:
        print(f"An error occurred while reading the file: {e}")
        sys.exit(1)

    if len(header_bytes) < 32:
        print(f"Error: The file '{file_path}' is too small to be a valid Hero Forge file.")
        sys.exit(1)

    # Unpack the header data. The format seems to be a mix of floats and integers.
    # We will unpack it in a few different ways to be sure we see the correct values.

    # Unpack as 8 floats (4 bytes each)
    floats = struct.unpack('<8f', header_bytes)

    # Unpack as 8 unsigned integers (4 bytes each)
    uints = struct.unpack('<8I', header_bytes)

    print("--- Hero Forge File Header Diagnostics ---")
    print(f"Analyzing file: {file_path}\n")

    print("Header data interpreted as 8 raw floats:")
    print(floats)
    print("\nHeader data interpreted as 8 raw unsigned integers:")
    print(uints)

    print("\n--- Analysis ---")
    print("Please provide this entire output to help resolve the parsing issue.")
    print("The 'raw unsigned integers' are the most likely to contain the correct data block sizes.")

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python diagnose.py <path_to_your_file.ckb>")
        sys.exit(1)

    diagnose_file(sys.argv[1])