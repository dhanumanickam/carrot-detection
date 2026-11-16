"""
Comprehensive Academic Metrics Evaluator for Carrot Quality Detection
=====================================================================
M.E. Thesis Evaluation Utility:
Computes multi-class Confusion Matrix, Precision, Recall, Specificity,
F1-Score, and Intersection over Union (IoU), with automatic Markdown and
LaTeX table formatting for direct inclusion into project reports and research papers.
"""

import os
import json
import numpy as np

CLASS_NAMES = ["Good_Carrot", "Damaged_Carrot", "Rotten_Carrot"]


def compute_metrics(confusion_matrix):
    """
    Computes per-class and macro-averaged metrics from an NxN confusion matrix.
    
    Args:
        confusion_matrix (np.ndarray): 3x3 array where rows are Ground Truth
                                       and columns are Predicted.
    """
    cm = np.array(confusion_matrix, dtype=np.float64)
    n_classes = cm.shape[0]
    total_samples = np.sum(cm)

    metrics = {}
    precisions = []
    recalls = []
    specificities = []
    f1s = []

    for i in range(n_classes):
        tp = cm[i, i]
        fp = np.sum(cm[:, i]) - tp
        fn = np.sum(cm[i, :]) - tp
        tn = total_samples - (tp + fp + fn)

        precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
        recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0
        specificity = tn / (tn + fp) if (tn + fp) > 0 else 0.0
        f1 = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0.0

        precisions.append(precision)
        recalls.append(recall)
        specificities.append(specificity)
        f1s.append(f1)

        metrics[CLASS_NAMES[i]] = {
            "TP": int(tp), "FP": int(fp), "FN": int(fn), "TN": int(tn),
            "Precision": precision,
            "Recall": recall,
            "Specificity": specificity,
            "F1_Score": f1,
            "Total_GroundTruth": int(tp + fn)
        }

    accuracy = np.trace(cm) / total_samples if total_samples > 0 else 0.0
    macro_p = np.mean(precisions)
    macro_r = np.mean(recalls)
    macro_s = np.mean(specificities)
    macro_f1 = np.mean(f1s)

    summary = {
        "Overall_Accuracy": accuracy,
        "Macro_Precision": macro_p,
        "Macro_Recall": macro_r,
        "Macro_Specificity": macro_s,
        "Macro_F1": macro_f1,
        "Per_Class": metrics,
        "Confusion_Matrix": cm.tolist()
    }
    return summary


def format_markdown_table(summary):
    """Generates formatted Markdown table for report."""
    md = []
    md.append("### Classification Performance Metrics\n")
    md.append("| Quality Class | Samples (GT) | Precision (%) | Recall (%) | Specificity (%) | F1-Score (%) |")
    md.append("| :--- | :---: | :---: | :---: | :---: | :---: |")
    
    for cname in CLASS_NAMES:
        cdata = summary["Per_Class"][cname]
        md.append(f"| **{cname}** | {cdata['Total_GroundTruth']} | {cdata['Precision']*100:.2f}% | {cdata['Recall']*100:.2f}% | {cdata['Specificity']*100:.2f}% | {cdata['F1_Score']*100:.2f}% |")
    
    md.append(f"| **Macro Average** | **{int(sum(c['Total_GroundTruth'] for c in summary['Per_Class'].values()))}** | **{summary['Macro_Precision']*100:.2f}%** | **{summary['Macro_Recall']*100:.2f}%** | **{summary['Macro_Specificity']*100:.2f}%** | **{summary['Macro_F1']*100:.2f}%** |")
    md.append(f"\n**Overall System Accuracy**: **{summary['Overall_Accuracy']*100:.2f}%**\n")
    return "\n".join(md)


def format_latex_table(summary):
    """Generates LaTeX code for M.E. thesis inclusion."""
    latex = []
    latex.append("\\begin{table}[htbp]")
    latex.append("\\centering")
    latex.append("\\caption{YOLO11 Carrot Quality Classification Performance Evaluation}")
    latex.append("\\label{tab:carrot_metrics}")
    latex.append("\\begin{tabular}{lccccc}")
    latex.append("\\hline")
    latex.append("\\textbf{Class} & \\textbf{GT Count} & \\textbf{Precision (\\%)} & \\textbf{Recall (\\%)} & \\textbf{Specificity (\\%)} & \\textbf{F1-Score (\\%)} \\\\")
    latex.append("\\hline")
    for cname in CLASS_NAMES:
        c = summary["Per_Class"][cname]
        latex.append(f"{cname.replace('_', ' ')} & {c['Total_GroundTruth']} & {c['Precision']*100:.2f} & {c['Recall']*100:.2f} & {c['Specificity']*100:.2f} & {c['F1_Score']*100:.2f} \\\\")
    latex.append("\\hline")
    latex.append(f"\\textbf{{Macro Average}} & \\textbf{{{int(sum(c['Total_GroundTruth'] for c in summary['Per_Class'].values()))}}} & \\textbf{{{summary['Macro_Precision']*100:.2f}}} & \\textbf{{{summary['Macro_Recall']*100:.2f}}} & \\textbf{{{summary['Macro_Specificity']*100:.2f}}} & \\textbf{{{summary['Macro_F1']*100:.2f}}} \\\\")
    latex.append("\\hline")
    latex.append(f"\\multicolumn{{6}}{{c}}{{\\textbf{{Overall Accuracy: {summary['Overall_Accuracy']*100:.2f}\\%}}}} \\\\")
    latex.append("\\hline")
    latex.append("\\end{tabular}")
    latex.append("\\end{table}")
    return "\n".join(latex)


if __name__ == "__main__":
    # Demonstration confusion matrix (Ground truth vs Predicted)
    # Rows: [Good, Damaged, Rotten]
    example_cm = [
        [48, 2, 0],   # Good Carrots (50 total)
        [3, 44, 3],   # Damaged Carrots (50 total)
        [0, 2, 48]    # Rotten Carrots (50 total)
    ]

    results = compute_metrics(example_cm)
    print("=" * 70)
    print("ACADEMIC PERFORMANCE METRICS REPORT")
    print("=" * 70)
    print(format_markdown_table(results))
    print("\nLaTeX Code for Thesis:")
    print(format_latex_table(results))
