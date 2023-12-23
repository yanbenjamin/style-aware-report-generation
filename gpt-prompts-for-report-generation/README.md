# GPT Prompts for Report Generation

### Preparation 

To get public submodules (`CXR-Report-Metric`) essential to this study, in this directory run 

```zsh
git add submodule https://github.com/rajpurkarlab/CXR-Report-Metric.git
```

Then, migrate the following script to the `CXR-Report-Metric` submodule. 

```
mv calc_metrics.py CXR-Report-Metric/
```

### Environment Setup and Infrastructure
To install the Python dependencies, create an environment with Python 3.7 (e.g. Conda env with `conda create -n new_env python=3.7` and `conda activate new_env`) and run

```zsh
pip install -r requirements.txt
```

As a note, if you are using newer GPUs with the NVIDIA sm_86 microarchitecture (e.g. Amperes), excise the installation of __torch==1.6.0__ from `requirements.txt`. Instead, run 

```zsh
pip install torch==1.10.0+cu113 -f https://download.pytorch.org/whl/cu113/torch_stable.html
```

to ensure CUDA compatibility with the torch version (check the <a href = "https://pytorch.org/">PyTorch website </a> for more information on CUDA and NVIDIA GPU compatibilities). 

On the infrastructure side, make sure to have an Azure OpenAI account, and a cloud-based deployed `gpt-3.5-turbo` model. For deployment details as well as pricing, see <a href = "https://learn.microsoft.com/en-us/azure/cognitive-services/openai/how-to/create-resource?pivots=web-portal">here</a> and <a href = "https://learn.microsoft.com/en-us/azure/cognitive-services/openai/quickstart?tabs=command-line&pivots=programming-language-python">here</a>. From the deployment, you will need the API key, base / endpoint value, and deployment name, which are described in the latter link.

### Report Generation 
We provide a command line interface for batching the report generation. To use the interface, follow these steps. 

First, make sure the environment is setup as described above. Then, run the `main.py` script, passing in your Azure OpenAI {API key, base / endpoint value, deployment name}, the input CSV file (with `serialization` and `id` columns for the predicted text serialization and MIMIC-CXR ID, respectively), a prompt stem string (which is appended at the beginning of each serialization to form the GPT prompt). You want to specify a cache directory (e.g., `./cache`; use `mkdir` if needed) to intermediately store generated reports, enclosed in separate `.txt` files. 

```zsh
python main.py --API_KEY <API Key> --DEPLOYMENT_NAME <Azure deployment name> --BASE <Azure base / endpoint> --input_csv mimic-cxr-test.csv --icl_csv mimic-cxr-icl.csv --num_icl_examples 1 --cache_dir cache --prompt_stem "Generate a chest x-ray report from the following key words:\n" --max_global_iter 10
```

Due to intermittent congestion in the OpenAI servers (where at some times, a request to generate a report may be delayed), there is a variable `--max_global_iter` that essentially runs a continual loop over all remaining reports to generate. Setting this to `10` (iterations) is usually a safe bet, though you *may* need to run the above command a few times to completely manufacture reports from all serializations (run `ls cache | wc` to see how many reports have been produced so far; note the value will be double if using in-context learning—see below—due to producing a `.txt` file for each report alongside a `.json` record of ICL examples).  

Also, if using in-context learning (ICL), you will want to input a CSV file with examples (similarly formatted to the input CSV along with an `original` column to pair serializations with ground truth reports) into `--icl_csv`, and specify the number of examples to use per report in `--num_icl_examples`. 

Other parameters can be inserted as well, including the GPT prompting configurations (e.g. temperature, max tokens, top_p) These are documented in the `main.py` source code. 

This Python program will pile the generated reports into the `cache` directory, which can you collate into a single CSV by running

```zsh
python helper.py collate_reports --cache_dir cache --input_csv mimic-cxr-test.csv --output_csv output.csv --num_icl_examples 1
```

All generated reports will fall under the `generated` column of the output CSV. All original columns from the input CSV are comprised in the output CSV as well.


### Report Evaluation

Evaluation metrics are provided through the `CXR-Report-Metric` submodule, as cloned from the <a href = https://github.com/rajpurkarlab/CXR-Report-Metric>eponymous repository</a>. You will want to follow the CheXbert and RadGraph setup instructions in that repo, namely

+ Download a pre-trained CheXbert model <a href = "https://stanfordmedicine.box.com/s/c3stck6w6dol3h36grdc97xoydzxd7w9">here</a>.
+ Download a pre-trained RadGraph model <a href = "https://physionet.org/content/radgraph/1.0.0/">here</a>.
+ Go into `./CXR-Report-Metric/config.py`, and set `CHEXBERT_PATH` and `RADGRAPH_PATH` to the absolute paths (or **relative** to the config file) of the downloaded CheXbert and RadGraph checkpoints, respectively.

After the steps in **Report Generation** that funnel the GPT-generated reports into `output.csv` (you may need to append a column `original` with the ground-truth reports), run 

```zsh
#splits the output.csv into the ground truth reports and the predicted reports (as generated by GPT)
python helper.py split_gt_predictions --csv_path output.csv --output_dir examples

#compares the ground truth & predicted reports for each RadGraph id and computes relevant metrics
cd CXR-Report-Metric
python calc_metrics.py --gt_reports "../examples/gt_reports.csv" --predicted_reports \
"../examples/predicted_reports.csv" --out_file "../radiology_metrics.csv" --use_idf False
```

This will create a CSV file `./radiology_metrics` in the git root directory, which contains the BLEU, BERT, SEMB, combined RadGraph, and RadCliQ scores for each generated report. To print out a performance summary,

```zsh
#return to the git root directory 
cd .. 
#logs the summary statistics to console for each metric
python helper.py summarize_metrics --metric_csv "radiology_metrics.csv"
```