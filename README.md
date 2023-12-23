# Style-Aware Radiology Report Generation 

Code used in the paper "Style-Aware Radiology Report Generation with RadGraph and Few-Shot Prompting" (Yan et. al, 2023). The repository is composed of the following primary modules: `report-radgraph-serialization` for producing text serializations of the radiology knowledge graphs (RadGraph), and `gpt-prompts-for-report-generation`, for prompting the large language model (LLM) to generate fully-fledged reports from RadGraph-based content representations. The image-to-text vision backbone model in the paper originates from (Nguyen et. al 2021), and you can find the repository [here](https://github.com/ginobilinie/xray_report_generation). Additionally, the code for medical report evaluation (Yu et. al 2023) can be found in the repository `CXR-Report-Metric` located [here](https://github.com/rajpurkarlab/CXR-Report-Metric).

Details for using each module are located within the respective directories's `README.md`, along with any additional setup information.

## Environment Setup and Infrastructure
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

## Citing 

If you are employing this repo, kindly cite this paper:

```bibtex
@inproceedings{yan-etal-2023-style,
    title = "Style-Aware Radiology Report Generation with {R}ad{G}raph and Few-Shot Prompting",
    author = "Yan, Benjamin  and
      Liu, Ruochen  and
      Kuo, David  and
      Adithan, Subathra  and
      Reis, Eduardo  and
      Kwak, Stephen  and
      Venugopal, Vasantha  and
      O{'}Connell, Chloe  and
      Saenz, Agustina  and
      Rajpurkar, Pranav  and
      Moor, Michael",
    booktitle = "Findings of the Association for Computational Linguistics: EMNLP 2023",
    month = dec,
    year = "2023",
    address = "Singapore",
    publisher = "Association for Computational Linguistics",
    url = "https://aclanthology.org/2023.findings-emnlp.977",
    doi = "10.18653/v1/2023.findings-emnlp.977",
    pages = "14676--14688",
}
```
