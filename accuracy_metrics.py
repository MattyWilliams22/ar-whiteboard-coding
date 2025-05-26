import re
from Levenshtein import distance as levenshtein_distance
import unicodedata
from collections import defaultdict
import csv
from datetime import datetime
import os


# --- Homoglyph Normalization ---
def normalise_homoglyphs(text):
    """Convert visually similar Unicode chars to their ASCII counterparts."""
    if text is None:
        return ""
    # Step 1: Unicode normalization (NFKC merges compatibility variants)
    normalised = unicodedata.normalize("NFKC", text)

    # Step 2: Custom mapping for critical symbols
    homoglyph_map = {
        # Fullwidth symbols → ASCII
        "＂": '"',
        "｛": "{",
        "｝": "}",
        "［": "[",
        "］": "]",
        "（": "(",
        "）": ")",
        "＠": "@",
        "＃": "#",
        "％": "%",
        "＆": "&",
        "＋": "+",
        "－": "-",
        "＝": "=",
        "＜": "<",
        "＞": ">",
        "＼": "\\",
        "＾": "^",
        "＿": "_",
        "｀": "`",
        "｜": "|",
        "～": "~",
        # Quotes and hyphens
        "‘": "'",
        "’": "'",
        "“": '"',
        "”": '"',
        "―": "-",
        "–": "-",
        # Math symbols
        "≠": "!=",
        "≤": "<=",
        "≥": ">=",
        "÷": "/",
        "×": "*",
    }

    return "".join(homoglyph_map.get(c, c) for c in normalised)


# --- Error Metrics ---
def calculate_accuracy_metrics(reference, ocr_output):
    """Calculate all accuracy metrics between reference and OCR output."""
    if reference is None or ocr_output is None:
        return {
            "cer": 1.0,
            "wer": 1.0,
            "symbol_accuracy": 0.0,
            "levenshtein_similarity": 0.0,
        }

    ref_norm = normalise_homoglyphs(reference)
    ocr_norm = normalise_homoglyphs(ocr_output)

    # Character Error Rate
    ref_len = len(ref_norm)
    cer = levenshtein_distance(ref_norm, ocr_norm) / ref_len if ref_len > 0 else 0.0

    # Word Error Rate
    ref_words = ref_norm.split()
    ocr_words = ocr_norm.split()
    wer = (
        levenshtein_distance(" ".join(ref_words), " ".join(ocr_words)) / len(ref_words)
        if ref_words
        else 0.0
    )

    # Symbol Accuracy
    symbols = "{}[]()<>@#*+-=!\"'/:\\"
    ref_sym = [c for c in ref_norm if c in symbols]
    ocr_sym = [c for c in ocr_norm if c in symbols]
    sym_acc = (
        sum(1 for r, o in zip(ref_sym, ocr_sym) if r == o) / len(ref_sym)
        if ref_sym
        else 1.0
    )

    # Levenshtein Similarity
    max_len = max(len(ref_norm), len(ocr_norm))
    lev_sim = (
        1 - (levenshtein_distance(ref_norm, ocr_norm) / max_len) if max_len > 0 else 1.0
    )

    return {
        "cer": cer,
        "wer": wer,
        "symbol_accuracy": sym_acc,
        "levenshtein_similarity": lev_sim,
    }


def save_metrics_to_csv(timing_data, accuracy_metrics):
    """Save both timing and accuracy metrics to a CSV file."""
    filename = "performance_metrics.csv"
    file_exists = os.path.isfile(filename)

    # Combine timing and accuracy data
    combined_data = {
        "timestamp": datetime.now().isoformat(),
        **timing_data,
        **accuracy_metrics,
        "success": timing_data.get("success", False),
    }

    # Ensure all expected fields are present
    default_fields = {
        "ground_truth_file": None,
        "cer": None,
        "wer": None,
        "symbol_accuracy": None,
        "levenshtein_similarity": None,
    }

    # Update with actual values while maintaining all fields
    for field in default_fields:
        if field not in combined_data:
            combined_data[field] = default_fields[field]

    # Write to CSV
    with open(filename, "a", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=combined_data.keys())
        if not file_exists:
            writer.writeheader()
        writer.writerow(combined_data)


def compare_with_ground_truth(generated_code, ground_truth_file):
    """Compare generated code with ground truth file."""
    if not os.path.exists(ground_truth_file):
        return None

    with open(ground_truth_file, "r", encoding="utf-8") as f:
        ground_truth = f.read()

    return calculate_accuracy_metrics(ground_truth, generated_code)


# --- Main Integration ---
def analyse_code_quality(python_code, ground_truth_path=None):
    """Analyse code quality and compare with ground truth if available."""
    metrics = {
        "cer": None,
        "wer": None,
        "symbol_accuracy": None,
        "levenshtein_similarity": None,
        "ground_truth_file": None,
    }

    if ground_truth_path:
        metrics["ground_truth_file"] = os.path.basename(ground_truth_path)
        ground_truth_metrics = compare_with_ground_truth(python_code, ground_truth_path)
        if ground_truth_metrics:
            metrics.update(ground_truth_metrics)

    return metrics
