"""
This module extracts and serializes graph data from a JSON file, providing a string report of each graph to a CSV file.
See the README for usage specifications.
"""

import json
import random
import argparse
import csv
import os
from tqdm import tqdm
from graph_report import serialize_graph_report

ERROR_LABELS, ERROR_METHOD = -1, -2 #constants used for error handling

def main(args):
    """
    Reads in a JSON file specified by the user, loops through every example in the file, 
    and outputs a CSV file containing the serialized graph reports for each example. 
    User specifies the serialization method used, which is not case sensitive in the CMD.  
    """
    # Read JSON file and load examples
    with open(args.json_path, "r") as f:
        json_str = f.read()
    examples = json.loads(json_str)

    # Open CSV file for writing
    with open(args.csv_path, "w", newline="") as f:
        writer = csv.writer(f)

        # Write header row to CSV
        writer.writerow(["id", "serialization", "full_report"])

        # Loop through each example in the JSON file
        for example_id, example in tqdm(examples.items()):
            report_serialization = serialize_graph_report(example, method = args.method_name.lower(),
                                                                     separate_findings = args.separate_findings) 
            report_full_text = example["text"]

            #error handling 
            if (report_serialization == ERROR_LABELS):
                raise ValueError("No entity labels provided for ID {}".format(example_id))
            elif (report_serialization == ERROR_METHOD):
                raise ValueError("invalid method specified (must be either subgraphs, no_sep, with_anat, with_@_anat)")
            
            # Write example ID and graph serializations to CSV
            writer.writerow([example_id, report_serialization, report_full_text])
    
    print("\nSaved out serializations to {}".format(os.path.abspath(args.csv_path)))

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--json_path", help="path to input JSON file")
    parser.add_argument("--csv_path", help="path to output CSV file")
    parser.add_argument("--method_name", help="serialization method (see README for method names & explanations)", default = "subgraphs")
    parser.add_argument("--separate_findings", help="whether to create sections for report findings and impressions", type = bool, default = True)
    args = parser.parse_args()

    main(args)