import fire
from CXRMetric.run_eval import calc_metric

def main(gt_reports = "../examples/gt_reports.csv",
         predicted_reports = "../examples/predicted_reports.csv",
         out_file = "../radiology_metrics.csv",
         use_idf = False):  
    
    calc_metric(gt_csv = gt_reports, pred_csv = predicted_reports, 
                out_csv = out_file, use_idf = use_idf)
    
if __name__ == "__main__":
    fire.Fire(main)