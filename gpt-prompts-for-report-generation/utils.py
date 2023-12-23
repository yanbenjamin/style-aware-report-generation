"""
a bundle of utility functions, mainly to garner examples for in-context learning
"""

import csv
import numpy as np

def tabulate_ICL_examples(icl_csv = "examples/test_serialized.csv", 
                          prompt_stem = "Generate a chest x-ray report from the following key words:\n", style_filter = None):
    """
    builds a list of in-context learning examples from a CSV of paired serializations and ground truth reports
    
    Args: 
        icl_csv (str): a CSV file with headers "serialization" and "original", with the latter referring to the
                        ground truth report 
        prompt_stem (str): The text that precedes the serialization when prompting the GPT.
        style_filter (list[str]): Optional. A list of keywords an in-context learning example
                        must contain (for style modulation purposes).
    
    Returns: 
        List[dict]: 
    """
    ICL_examples = []
    serialization_col_idx = None
    original_col_idx = None
    with open(icl_csv,"r") as file: 
        reader = csv.reader(file)
        for row_ix, row in enumerate(reader):
            if (row_ix == 0): #header row, identify relevant column indices
                serialization_col_idx = row.index("serialization")
                original_col_idx = row.index("original")
                id_col_idx = row.index("id")
                
            report_text = row[original_col_idx]
            serialization_text = row[serialization_col_idx]
            image_id = row[id_col_idx]
            
            ICL_examples.append({"id": image_id, "example": (prompt_stem + serialization_text, report_text)})
            
    return ICL_examples

def get_ICL_examples(ICL_data, num_icl_examples = 1):
    #randomly sample num_icl_examples from the total bank of in-context learning pairs
    rand_idx = np.random.choice(range(len(ICL_data)), size = num_icl_examples, replace = False)
    icl_pairs = [ICL_data[idx] for idx in rand_idx]

    #break the data into a list of report IDs and a list of example pairs (serialization, report)
    in_context_ids = [icl_example["id"] for icl_example in icl_pairs]
    in_context_examples = [icl_example["example"] for icl_example in icl_pairs]
    
    return in_context_ids, in_context_examples

if __name__ == "__main__":
    pass