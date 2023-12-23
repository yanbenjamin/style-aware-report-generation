"""helper suite for tools related to medical report generation
(e.g. viewing the generated reports in command line)

To call a specific function listed below, run 
python helper.py <function_name> --<parameter1> <value1> --<parameter2> <value2> ...
"""

import csv
import os 
import fire
import sys
import pandas as pd
import numpy as np
import json
import glob
from tqdm import tqdm

def list_ids(csv_path = "output.csv", 
             id_col_name = "id"):
    """
    prints to console all the IDs prevalent in a report CSV
    
    Args:
        csv_path (str): a CSV file containing the medical reports 
        id_col_name (str): column name within the CSV storing the report IDs
    """
    df = pd.read_csv(csv_path)
    ids = list(df[id_col_name])
    print("Report IDs: {}".format(ids))

def view_report(csv_path = "output.csv",
                gt_col_name = "original",
                predicted_col_name = "generated",
                id_col_name = "id",
                serialization_col_name = "serialization",
                radgraph_id = None):
    """
    prints to console the ground truth report and the GPT-predicted report texts, 
    given a specific RadGraph id and a CSV containing those reports
    
    Args:
        csv_path (str): a CSV file containing the predicted and ground truth medical reports
        gt_col_name (str): column name within the CSV storing the ground truth (original) reports
        predicted_col_name (str): column name within the CSV storing the predicted / generated reports
        id_col_name (str): column name within the CSV storing the RadGraph ids
        radgraph_id (str): specific ID to query for its reports
    
    Returns:
        None
    """
    df = pd.read_csv(csv_path, index_col = id_col_name)
    if radgraph_id not in df.index:
        raise ValueError("Provided Radgraph ID not in reports CSV")
        
    data = df.loc[radgraph_id]
    
    print("Original Medical Report\n------------------")
    print(data[gt_col_name])
    print("\nSerialization Report\n------------------")
    print(data[serialization_col_name])
    print("\nGPT-Generated Medical Report\n------------------")
    print(data[predicted_col_name])

def split_gt_predictions(csv_path = "output.csv",
                output_dir = "CXR-Report-Metric/reports",
                gt_col_name = "original",
                predicted_col_name = "generated",
                id_col_name = "id"):
    """
    takes the CSV output by the report generation script, and divides
    it into two separate CSVs: one for the original reports (gt_reports.csv), 
    the other for the predicted reports by GPT (predicted_reports.csv). 

    Args:
        csv_path (str): a filepath to the CSV with the generated medical reports
        output_dir (str): path to the directory to save out the two CSVs
        gt_col_name (str): column name within the CSV storing the ground truth (original) reports
        predicted_col_name (str): column name within the CSV storing the predicted / generated reports
        id_col_name (str): column name within the CSV storing the RadGraph ID
    
    Returns:
        None
    """
    
    df = pd.read_csv(csv_path)
    
    #separate the ground truth and prediction reports
    list_ids = list(range(len(df)))
    
    gt_reports = list(df[gt_col_name])
    df_groundtruth_dict = {"study_id": list_ids, "id": list(df[id_col_name]), "report": gt_reports}
    
    df_predicted_dict = {"study_id": list_ids, "id": list(df[id_col_name]), "report": list(df[predicted_col_name])}

    df_gt = pd.DataFrame.from_dict(df_groundtruth_dict)
    df_predicted = pd.DataFrame.from_dict(df_predicted_dict)
    
    #save out the Pandas dataframes to individual .csv files housed in the output_dir
    gt_filepath = os.path.join(output_dir, "gt_reports.csv")
    df_gt.to_csv(gt_filepath)
    predicted_filepath = os.path.join(output_dir, "predicted_reports.csv")
    df_predicted.to_csv(predicted_filepath)
    
    print("Saved ground truth CSV to {}".format(gt_filepath))
    print("Saved predicted CSV to {}".format(predicted_filepath))

def collate_reports(cache_dir = "./cache/reports_0", 
                    input_csv = "examples/mimic-cxr-pipeline.csv",
                    output_csv = "out.csv",
                    num_icl_examples = 0):
    """
    collates the generated report files into one CSV, which modifies the original input CSV 
    into main.py / parallel_generator.py by including an extra column ("generated")
    
    Args:
        cache_dir (str): directory path where the .txt predicted reports are stored
        input_str (str): path to the input CSV that was previously passed into main.py / parallel_generator.py
        output_csv (str): path to store the new CSV file with the generated reports included
        num_icl_examples (int): number of in-context learning examples used for each generation
    
    Returns: 
        None
    """
    
    df_original = pd.read_csv(input_csv)
    report_files = glob.glob(os.path.join(cache_dir, "*.txt"))
    generated_report_ids = [fname.split("/")[-1].replace("_","/") for fname in report_files]
    
    #read through each of the generated report .txts and collect them in a Pandas dataframe
    data_generated = {"id": generated_report_ids, "generated": []}
    if (num_icl_examples > 0): 
        data_generated.update({f"icl_{str(i).zfill(3)}": [] for i in range(num_icl_examples)})
    
    for report_file in report_files:
        with open(report_file,"r") as file:
            data_generated["generated"].append(file.read())
        
        if (num_icl_examples == 0):
            continue 
            
        #include ICL metadata in the CSV if in-context learning was used
        metadata_file = report_file.replace(".txt",".json")
        with open(metadata_file,"r") as file: 
            icl_examples = json.load(file)["ICL_ids"]
        for i in range(num_icl_examples):
            data_generated[f"icl_{str(i).zfill(3)}"].append(icl_examples[i])
            
    df_generated = pd.DataFrame.from_dict(data_generated)
    
    #merge the original dataframe with the new one containing the predicted reports
    df_joint = pd.merge(df_original, df_generated, how="inner", left_on = "id", right_on = "id")
    print(f"Number of Reports Collated: {len(df_joint)}")
    print(df_joint.head(20))
    
    #save to a new CSV file 
    df_joint.to_csv(output_csv, index = False)
    
def summarize_metrics(metric_csv = "radiology_metrics.csv", use_API = False):
    """
    calculates summary statistics (e.g. mean, standard deviation, median, inter-quartile range)
    for each of the radiological metrics present in the evaluation CSV. these statistics 
    are printed to the console. 
    
    Args:
        metric_csv (str): filepath to the CSV created by the CXR-Report-Metric module, 
                          containing summary metrics for each of the GPT-predicted reports. 
    
    Returns:
        None (if using the API mode, then a dictionary containing the summarty stats and raw values)
    """
    df = pd.read_csv(metric_csv)
    metrics = ["bleu_score", "bertscore", "semb_score", "radgraph_combined", "RadCliQ"]
    
    metrics_dict = {}
    raw_dict = {}
    for metric in metrics: 
        data = df[metric]
        mean, std, median = float(np.mean(data)), float(np.std(data)), float(np.median(data))
        #interquartile range
        quartile_25, quartile_75 = np.percentile(data, [25,75])
        IQR = float(quartile_75 - quartile_25)
        if (use_API == False):
            print("{} | mean: {:.3f} | std: {:.3f} | median: {:.3f} | IQR: {:.3f} | n: {}".format(
                metric, mean, std, median, IQR, len(data)))
        metrics_dict[metric] = {"mean": mean, "std": std, "median": median, "IQR": IQR, "n": len(data), "raw": list(data)}
    
    if (use_API == True):
        return metrics_dict

def log_metrics(csv_files = "radiology_metrics.csv", 
                out_file = "radiology.json"):
    """
    logs out summary statistics for a series of csv files (output by CXR-Report-Metric module)
    into a unified JSON file, as well as the raw numbers for each individual report
    
    Args:
        csv_files (str): a sequence of space-separated csv file paths
        out_file (str): a json file path where to store the logged statistics
    
    Returns:
        None
    """
    summary_data = {}
    csv_files = [fname.strip() for fname in csv_files.split(" ")]
    
    for csv_file in csv_files:
        print("Summarized {}".format(csv_file))
        summary_data[csv_file] = summarize_metrics(csv_file, use_API = True)
    
    with open(out_file,"w") as file: 
        #save out the summary data as a JSON file
        json.dump(summary_data, file, indent = 4)
    
    print("Summary statistics logged to {}".format(os.path.abspath(out_file)))
    
if __name__ == "__main__":
    fire.Fire()