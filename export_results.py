import os
import csv
import sys

# Define the output CSV file name
output_csv = "summary.csv"

# Define the column headers
headers = ["model", "nr states", "nr actions", "mem size", "total members", "sat members", "time"]

# Function to parse the content of the file and extract required information
def parse_file_content(file_path):
    try:
        with open(file_path, "r") as f:
            lines = f.readlines()

        # Extract relevant data from the last part of the file
        nr_states = None
        nr_actions = None
        sat_members = None
        total_members = None
        time = None

        for line in lines:
            if "constructed explicit quotient" in line and "states" in line and "choices" in line:
                parts = line.split("constructed explicit quotient having")[1].strip().split("and")
                nr_states = int(parts[0].split("states")[0].strip())
                nr_actions = int(parts[1].split("choices")[0].strip())
            elif "family size:" in line:
                family_size = int(line.split("family size:")[1].strip().split(",")[0])
            elif "satisfied" in line and "members" in line:
                sat_members = int(line.split("satisfied")[1].split("/")[0].strip())
                total_members = int(line.split("satisfied")[1].split("/")[1].split("members")[0].strip())
            elif "time:" in line:
                time = float(line.split("time:")[1].strip().split(" ")[0])

        return [
            os.path.splitext(os.path.basename(file_path))[0],
            nr_states if nr_states is not None else "",
            nr_actions if nr_actions is not None else "",
            file_path[-5],
            total_members if total_members is not None else "",
            sat_members if sat_members is not None else "",
            time if time is not None else ""
        ]
    except Exception as e:
        print(f"Error parsing file {file_path}: {e}")
        return None

# Get the folder path from the command line arguments
if len(sys.argv) < 2:
    print("Usage: python script.py <folder_path>")
    sys.exit(1)

folder_path = sys.argv[1]

# Get the list of files in the specified folder
files = [os.path.join(folder_path, f) for f in os.listdir(folder_path) if os.path.isfile(os.path.join(folder_path, f)) and f.endswith(".log")]

# Prepare the data for the CSV file
data = []
for file in files:
    parsed_data = parse_file_content(file)
    if parsed_data:
        data.append(parsed_data)

# Write the data to the CSV file
with open(output_csv, mode="w", newline="") as csv_file:
    writer = csv.writer(csv_file)
    writer.writerow(headers)  # Write the headers
    writer.writerows(data)   # Write the rows

print(f"CSV file '{output_csv}' has been created with {len(data)} entries.")