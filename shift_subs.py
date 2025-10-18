#source: google gemini
#shifts all subtitles in a .srt file by the given amount. 
#example: python shift_subs.py file.srt -0.5 advances all subtitles by 0.5s.
#example: python shift_subs.py -a -0.5 does the same, but for all .srt files in the current directory.

import sys
import re
import os
from datetime import timedelta
from glob import glob

def time_to_timedelta(time_str):
    """Converts an 'HH:MM:SS,mmm' time string to a timedelta object."""
    # The regex splits the time string into hours, minutes, seconds, and milliseconds
    match = re.match(r'(\d{2}):(\d{2}):(\d{2}),(\d{3})', time_str)
    if match:
        hours, minutes, seconds, milliseconds = map(int, match.groups())
        return timedelta(hours=hours, minutes=minutes, seconds=seconds, milliseconds=milliseconds)
    return timedelta()

def timedelta_to_time(td):
    """Converts a timedelta object back to an 'HH:MM:SS,mmm' time string."""
    total_milliseconds = int(td.total_seconds() * 1000)
    if total_milliseconds < 0:
        # Cap negative time at '00:00:00,000' as SRT doesn't support negative times
        return '00:00:00,000'

    hours = total_milliseconds // 3600000
    total_milliseconds %= 3600000
    minutes = total_milliseconds // 60000
    total_milliseconds %= 60000
    seconds = total_milliseconds // 1000
    milliseconds = total_milliseconds % 1000

    return f"{hours:02}:{minutes:02}:{seconds:02},{milliseconds:03}"

def format_shift_suffix(shift_seconds):
    """Creates a clean, file-system-safe string representing the shift amount."""
    # Convert the shift to a string, replace dots with underscores for filename safety,
    # and prepend 'plus' or 'minus'.
    sign = 'minus' if shift_seconds < 0 else 'plus'
    abs_shift = str(abs(shift_seconds)).replace('.', '_')
    return f"_shifted_{sign}{abs_shift}"

def shift_subtitle_file(input_file, shift_seconds):
    """
    Shifts all time codes in a single SRT file by the specified number of seconds
    and creates a new file with a descriptive suffix.

    :param input_file: Path to the original SRT file.
    :param shift_seconds: Time shift in seconds (can be positive or negative).
    :return: The path to the newly created, shifted file, or None on failure.
    """
    if not input_file.lower().endswith('.srt'):
        print(f"Skipping '{input_file}': Not an SRT file.")
        return None
        
    # --- New Filename Logic ---
    shift_suffix = format_shift_suffix(shift_seconds)
    base, ext = os.path.splitext(input_file)
    output_file = base + shift_suffix + ext
    
    # Convert the shift amount to a timedelta object
    shift_delta = timedelta(seconds=shift_seconds)
    
    # Regex to find the time codes line: "HH:MM:SS,mmm --> HH:MM:SS,mmm"
    time_line_pattern = re.compile(r'(\d{2}:\d{2}:\d{2},\d{3}) --> (\d{2}:\d{2}:\d{2},\d{3})')
    
    print(f"\nProcessing '{input_file}'...")
    print(f"  Adjustment: {shift_seconds} seconds.")

    try:
        with open(input_file, 'r', encoding='utf-8') as infile, \
             open(output_file, 'w', encoding='utf-8') as outfile:
            
            for line in infile:
                match = time_line_pattern.match(line)
                
                if match:
                    # Found a time code line, extract start and end
                    start_time_str, end_time_str = match.groups()
                    
                    # Apply the shift
                    new_start_td = time_to_timedelta(start_time_str) + shift_delta
                    new_end_td = time_to_timedelta(end_time_str) + shift_delta
                    
                    # Convert back to formatted time strings
                    new_start_time_str = timedelta_to_time(new_start_td)
                    new_end_time_str = timedelta_to_time(new_end_td)
                    
                    # Write the new time code line
                    new_line = f"{new_start_time_str} --> {new_end_time_str}\n"
                    outfile.write(new_line)
                else:
                    # Write all other lines as is
                    outfile.write(line)

        print(f"  ✅ New shifted file created: **{output_file}**")
        return output_file

    except FileNotFoundError:
        print(f"  ❌ Error: Input file '{input_file}' not found. Skipping.")
        return None
    except Exception as e:
        print(f"  ❌ An unexpected error occurred while processing '{input_file}': {e}")
        return None

def main():
    """Main function to handle command-line arguments and run the shift."""
    args = sys.argv[1:]
    all_files_mode = '-a' in args

    if all_files_mode:
        # Expected: script.py -a <shift>
        if len(args) != 2:
            print("Usage for All Files Mode: python script.py -a <shift_amount_seconds>")
            print("Example: python script.py -a -0.8")
            sys.exit(1)
            
        shift_arg = next((arg for arg in args if arg != '-a'), None)
        input_files = glob('*.srt') # Find all .srt files in the current directory
        
        if not input_files:
            print("❌ No .srt files found in the current directory.")
            sys.exit(0)

    else:
        # Expected: script.py <file.srt> <shift>
        if len(args) != 2:
            print("Usage for Single File Mode: python script.py <input_file.srt> <shift_amount_seconds>")
            print("Example: python script.py my_subs.srt 1.5")
            sys.exit(1)
            
        input_file = args[0]
        shift_arg = args[1]
        input_files = [input_file]
        
    # Validate the shift amount
    try:
        shift_seconds = float(shift_arg)
    except ValueError:
        print(f"❌ Error: Shift amount '{shift_arg}' must be a number (float or integer).")
        sys.exit(1)
    
    # --- Execute the shift operation for all collected files ---
    print(f"--- Starting Subtitle Time Shift ---")
    print(f"Mode: {'All SRT Files in Current Directory' if all_files_mode else 'Single File'}")
    print(f"Adjustment: {shift_seconds} seconds ({'Advance (Move Earlier)' if shift_seconds < 0 else 'Delay (Move Later)'})")
    print("-" * 35)

    processed_count = 0
    for f in input_files:
        if shift_subtitle_file(f, shift_seconds):
            processed_count += 1

    print("\n--- Subtitle Shifting Complete ---")
    print(f"Successfully processed {processed_count} file(s).")
    print("Original file(s) remain unmodified.")


if __name__ == "__main__":
    main()