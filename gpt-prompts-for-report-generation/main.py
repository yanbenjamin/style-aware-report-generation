"""
Generates reports to a shared directory 
in the form of .txt files, which can be collated using collate_reports() in <helper.py>
"""

import openai
import time 
import multiprocessing as mp
from tqdm import tqdm
import argparse
import fire
import pandas as pd
import numpy as np
import glob
import os
from utils import tabulate_ICL_examples, get_ICL_examples
import json

def write_report(radgraph_id):
    """
    for a given RadGraph ID, inserts the serialization into the large language model,
    generates the stylized report, and saves it to the cache
    """
    prompt = prompts[radgraph_id]
    id = radgraph_id.replace("/","_")

    messages = [{"role": "system", "content": "You are a helpful assistant that generates chest x-ray reports from key words."}]
    
    #add in-context learning examples
    in_context_ids = None
    if examples_per_generation > 0:
        in_context_ids, in_context_examples = ICL_data_assigned[id.replace("_","/")]
        for example_prompt, example_output in in_context_examples:
            messages.append({"role": "user", "content": example_prompt}) #serialization 
            messages.append({"role": "assistant", "content": example_output}) #ground truth report
    
    messages.append({"role": "user", "content": f"{prompt}"})
    
    try:
        completion = openai.ChatCompletion.create(
                engine = deployment_name,
                messages=messages,
                **config)
        report = completion["choices"][0]["message"]["content"]
    except:
        time.sleep(5)
        return 

    with open(os.path.join(cache_directory, id), "w") as file:
        file.write(report)
        
    if (in_context_ids != None):
        with open(os.path.join(cache_directory, id).replace(".txt",".json"), "w") as file:
            json.dump({"ICL_ids": in_context_ids}, file)

def generate_reports_pool(threadpool_size, buffer_size = 30):
    """
    assembles a threadpool of report-generating threads
    """
    ids = list(prompts.keys())
    with mp.Pool(threadpool_size) as p:
        L = list(tqdm(p.imap(write_report, ids), total = buffer_size))
   
def reduce_prompts_queue(radgraph_ids):
    """
    determines which reports still need to be generated
    based on the files that are already in the cache 
    """
    cached_files = glob.glob(os.path.join(cache_directory, "*.txt"))
    generated_radgraph_ids = [fname.split("/")[-1].replace("_","/") for fname in cached_files]
    reports_remaining = set(radgraph_ids).difference(generated_radgraph_ids)
    global prompts
    prompts = {key:value for key,value in prompts.items() if key in reports_remaining}
    return len(radgraph_ids) - len(reports_remaining)

def main(API_KEY = "",
         DEPLOYMENT_NAME = "",
         BASE = "",
        max_tokens = 300,
         temperature = 0.5,
         top_p = 1,
         model = "gpt-3.5-turbo",
         input_csv = "examples/mimic-dev.csv",
         icl_csv = "examples/mimic-icl.csv", 
         num_icl_examples = 0,
         delimiter_csv = ",",
         cache_dir = "./cache/reports_0",
         prompt_stem = "Generate a chest x-ray report from the following key words:\n",
         threadpool_size = 5,
         max_global_iter = 3
        ):
    """
    This function ingests the RadGraph serializations from an input CSV, and saves out
    a CSV with a new column containing the GPT-generated medical reports. 
    
    Args:
        API_Key (str): Your Azure OpenAI API key. 
        DEPLOYMENT_NAME (str): Name of the Azure OpenAI deployment
        BASE (str): Name of the Azure OpenAI base / endpoint value
        API_Key (str): Your Azure OpenAI API key. 
        max_tokens (int): Maximum token per generated report.
        temperature (float): Parameter for adjusting the softmax in GPT's auto-regressive predictions.
        top_p (int): Controlling the randomness of the generated text. 
        model (str): Name of GPT model used for prompting (e.g. gpt-3.5-turbo, gpt-4)
        input_csv (str): File path for the input CSV indexed by report ID. The CSV should have a
                            column "serialization" containing the serialized graph representations.
        delimiter_csv (str): Delimiter for the input CSV file
        prompt_stem (str): The text that precedes the serialization when prompting the GPT.
        threadpool_size (int): Number of threads in the GPT-parallelizing threadpool
        
    Return:
        None
    """

    #set up the Azure OpenAI configuration
    openai.api_key = API_KEY
    openai.api_base = BASE
    openai.api_type = 'azure'
    openai.api_version = '2023-05-15' 
    
    global deployment_name 
    deployment_name= DEPLOYMENT_NAME

    global config 
    config = {'temperature': temperature, 'top_p': top_p, 'max_tokens': max_tokens}
    global cache_directory
    cache_directory = cache_dir
    
    #set up the global variables involving in-context learning data for the threadpool
    ICL_data = tabulate_ICL_examples(icl_csv, prompt_stem) if num_icl_examples > 0 else None
    global examples_per_generation
    examples_per_generation = num_icl_examples
    
    #set up the prompts for GPT using the serializations in the input CSV
    df = pd.read_csv(input_csv)
    n = len(df)
    radgraph_ids, radgraph_serializations = list(df["id"]), list(df["serialization"])
    global prompts
    prompts = {}
    for i in tqdm(range(n)):
        prompts[radgraph_ids[i]] = prompt_stem + radgraph_serializations[i]
    
    #check the reports in the cache directory that have already
    #been generated
    num_reports_generated = reduce_prompts_queue(radgraph_ids)
    print(f"\nReports Remaining To Generate: {n - num_reports_generated} out of {n}")
    
    #dispatch in-context learning examples for each remaining prompt
    global ICL_data_assigned
    ICL_data_assigned = {id: get_ICL_examples(ICL_data, examples_per_generation) for id in radgraph_ids} if examples_per_generation > 0 else None
    ICL_data = None
    
    #iterate through the remaining reports that need to be 
    #generated, ending when all are completed or a maximum number
    #of iterations has been reached
    global_iter = 0
    while (num_reports_generated < n and global_iter < max_global_iter):
        global_iter += 1
        
        #generate reports using a threadpool
        generate_reports_pool(threadpool_size)
        
        #count the remaining reports and reduce the queue accordingly
        num_reports_generated = reduce_prompts_queue(radgraph_ids)
        print(f"\nReports Remaining To Generate: {n - num_reports_generated} out of {n}")
        
if __name__ == "__main__":
    fire.Fire(main)