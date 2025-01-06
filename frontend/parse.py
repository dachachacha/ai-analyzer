#!/usr/bin/env python3

import os
import subprocess
import argparse
import sys

def run_tree(f_out, excluded_dirs):
    """
    Executes the `tree -L 6` command excluding specified directories
    and writes its output to the provided file handle.
    """
    try:
        # Create the exclusion pattern by joining all excluded directories with '|'
        exclusion_pattern = '|'.join(excluded_dirs)
        
        # Run the tree command with depth level 6 and exclude specified directories
        result = subprocess.run(
            ['tree', '-L', '6', '-I', exclusion_pattern],
            capture_output=True,
            text=True,
            check=True
        )
        f_out.write(result.stdout)
    except FileNotFoundError:
        f_out.write("Error: The 'tree' command is not found. Please install it and try again.\n")
    except subprocess.CalledProcessError as e:
        f_out.write(f"Error executing tree command: {e}\n")

def print_separator(f_out):
    """
    Writes a separator line consisting of underscores to the provided file handle.
    """
    f_out.write('_' * 80 + '\n')  # Adjust the number of underscores as needed

def is_excluded_dir(dir_name, excluded_dirs_set):
    """
    Determines if a directory should be excluded.
    Excludes directories present in the excluded_dirs_set.
    """
    return dir_name in excluded_dirs_set

def is_excluded_file(file_name, excluded_files_set):
    """
    Determines if a file should be excluded based on its extension
    or if it's explicitly listed in the excluded_files_set.
    """
    excluded_extensions = {
        '.lock', '.json', '.ico','.svg',
        '.doc', '.docx', '.pdf', '.png', '.jpg', '.jpeg', 
        '.gif', '.exe', '.zip', '.tar', '.gz', '.ppt', '.pptx'
    }
    _, ext = os.path.splitext(file_name.lower())
    return file_name in excluded_files_set or ext in excluded_extensions

def parse_files(f_out, excluded_dirs_set, excluded_files_set, input_files=None):
    """
    Parses specified input files or all .txt files in the current directory if no input files are provided.
    Excludes specified directories, specific files, and non-txt files.
    For each valid file, writes its name and contents to the provided file handle.
    """
    if input_files:
        files_to_process = input_files
    else:
        # If no input files are specified, walk through the directory
        files_to_process = []
        for root, dirs, files in os.walk('.', topdown=True):
            # Modify dirs in-place to exclude specified directories
            dirs[:] = [d for d in dirs if not is_excluded_dir(d, excluded_dirs_set)]
            for file in files:
                if is_excluded_file(file, excluded_files_set):
                    continue  # Skip excluded files
                file_path = os.path.join(root, file)
                files_to_process.append(file_path)

    for file_path in files_to_process:
        # If input_files are specified, ensure they are not within excluded directories
        if input_files:
            # Check if the file is within an excluded directory
            parts = file_path.split(os.sep)
            if any(part in excluded_dirs_set for part in parts):
                continue  # Skip files within excluded directories

        # Convert to relative path and use forward slashes
        rel_path = os.path.relpath(file_path, '.').replace(os.sep, '/')
        if not rel_path.startswith('.'):
            rel_path = f"./{rel_path}"
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
                line_count = len(lines)
                contents = ''.join(lines)
            # Modified line to include the number of lines
            f_out.write(f"FILE: {rel_path} ({line_count} lines)\n")
            f_out.write("FILE_CONTENTS:\n")
            f_out.write(contents + '\n')
        except UnicodeDecodeError:
            f_out.write(f"FILE: {rel_path} (Unable to determine line count)\n")
            f_out.write("Error: File is not a text file or contains invalid characters.\n")
        except Exception as e:
            f_out.write(f"FILE: {rel_path} (Unable to determine line count)\n")
            f_out.write(f"Error reading file: {e}\n")
        f_out.write('\n')  # Add an empty line between files

def parse_arguments():
    """
    Parses command-line arguments.
    Returns the output file path, list of input files, and list of additional excluded directories/files specified by the user.
    """
    parser = argparse.ArgumentParser(
        description="AI-Powered IAM Advisor File Parser",
        epilog="Example usage: ./iam_advisor.py -o /path/to/output.txt -f file1.txt file2.txt -x docs temp file3.txt"
    )
    parser.add_argument(
        '-o', '--output',
        type=str,
        default='/tmp/file_contents.txt',
        help="Path to the output file (default: /tmp/file_contents.txt)"
    )
    parser.add_argument(
        '-f', '--files',
        type=str,
        nargs='+',
        help="List of input .txt files to process"
    )
    parser.add_argument(
        '-x', '--exclude',
        type=str,
        nargs='*',
        default=[],
        help="Additional directories or specific files to exclude (e.g., docs temp file1.txt)"
    )
    args = parser.parse_args()
    return args.output, args.files, args.exclude

def main():
    """
    Main function to execute the script steps.
    All output is written to the specified output file.
    If input files are specified, only those files are processed and tree output is excluded.
    Additional directories and files can be excluded using the -x flag.
    """
    output_file, input_files, additional_excluded_items = parse_arguments()
    
    # Base excluded directories
    base_excluded_dirs = {'node_modules', '.git', 'documentation'}
    # Initialize sets for excluded directories and files
    excluded_dirs_set = set()
    excluded_files_set = set()
    # Add additional excluded directories and files from -x flag
    for item in additional_excluded_items:
        # Check if the item is a directory
        if os.path.isdir(item):
            excluded_dirs_set.add(item)
        # Check if the item is a file
        elif os.path.isfile(item):
            excluded_files_set.add(os.path.basename(item))
        else:
            # If the item is neither a file nor a directory, assume it's a directory or a file name
            # Here, you can choose to handle it as needed. For simplicity, we'll add it to both.
            excluded_dirs_set.add(item)
            excluded_files_set.add(item)
    
    # Union the base excluded directories with additional excluded directories
    excluded_dirs_set = base_excluded_dirs.union(excluded_dirs_set)
    
    try:
        with open(output_file, 'w', encoding='utf-8') as f_out:
            if not input_files:
                # No input files specified; include tree output
                run_tree(f_out, excluded_dirs_set)
                print_separator(f_out)
            else:
                # Input files specified; exclude tree output
                pass  # Do not run tree
            parse_files(f_out, excluded_dirs_set, excluded_files_set, input_files)
            if not input_files:
                print_separator(f_out)
            f_out.write("Just correct errors and inconsistencies please.\n")
        print(f"Output successfully saved to {output_file}")
    except PermissionError:
        print(f"Error: Permission denied when trying to write to {output_file}.")
    except FileNotFoundError as e:
        print(f"Error: {e}")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")

if __name__ == "__main__":
    main()

