# Style-Aware Radiology Report Generation 

Code used in the paper "Style-Aware Radiology Report Generation with RadGraph and Few-Shot Prompting" (Yan et. al, 2023). The repository is composed of the following primary modules: `report-radgraph-serialization` for producing text serializations of the radiology knowledge graphs (RadGraph), and `gpt-prompts-for-report-generation`, for prompting the large language model (LLM) to generate fully-fledged reports from RadGraph-based content representations. The image-to-text vision backbone model in the paper originates from (Nguyen et. al 2021), and you can find the repository [here](https://github.com/ginobilinie/xray_report_generation). Additionally, the code for medical report evaluation (Yu et. al 2023) can be found in the repository `CXR-Report-Metric` located [here](https://github.com/rajpurkarlab/CXR-Report-Metric).

Details for using each module are located within the respective directories's `README.md`, along with infrastructure and environment setup information.

# Citing 

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
