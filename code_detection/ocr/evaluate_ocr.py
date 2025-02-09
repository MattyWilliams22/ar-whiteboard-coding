import os
import cv2
import numpy as np
import json
import editdistance
from sklearn.metrics import precision_recall_fscore_support

# Import OCR methods
from paddle_ocr import test_detection as detect_paddleocr_text
from easy_ocr import test_detection as detect_easyocr_text
from py_tesseract import test_detection as detect_pytesseract_text
from kerasocr import test_detection as detect_kerasocr_text
from trocr import test_detection as detect_trocr_text

# Define the paths to the IAM dataset (assuming images and ground truth text are in the correct folders)
IAM_TEST_PATH = 'dataset/data/'

# Function to calculate word-level accuracy
def word_level_accuracy(detected_text, ground_truth):
    detected_words = detected_text.split()
    ground_truth_words = ground_truth.split()
    correct_words = sum([1 for dw, gw in zip(detected_words, ground_truth_words) if dw == gw])
    return correct_words / len(ground_truth_words) if len(ground_truth_words) > 0 else 0

# Function to calculate character-level accuracy
def character_level_accuracy(detected_text, ground_truth):
    correct_chars = sum([1 for dc, gc in zip(detected_text, ground_truth) if dc == gc])
    return correct_chars / len(ground_truth) if len(ground_truth) > 0 else 0

# Function to calculate Word Error Rate (WER)
def word_error_rate(ref, hyp):
    ref_words = ref.split()
    hyp_words = hyp.split()
    S = sum(1 for r, h in zip(ref_words, hyp_words) if r != h)
    D = len(ref_words) - len(hyp_words)
    I = len(hyp_words) - len(ref_words)
    return (S + D + I) / len(ref_words) if len(ref_words) > 0 else 0

# Function to calculate Character Error Rate (CER)
def char_error_rate(ref, hyp):
    S = sum(1 for r, h in zip(ref, hyp) if r != h)
    D = len(ref) - len(hyp)
    I = len(hyp) - len(ref)
    return (S + D + I) / len(ref) if len(ref) > 0 else 0

# Function to evaluate OCR and output various metrics
def evaluate_ocr(ocr_method, results_file):
    word_accuracies = []
    char_accuracies = []
    lev_distances = []
    word_errors = []
    char_errors = []
    
    with open(os.path.join(IAM_TEST_PATH, 'ground_truth.json'), 'r') as f:
        ground_truth_data = json.load(f)
    
    # Iterate over the IAM test samples
    for sample in ground_truth_data:
        image_path = os.path.join(IAM_TEST_PATH, sample['image'])
        ground_truth = sample['ground_truth']
        
        image = cv2.imread(image_path)
        detected_text = ocr_method(image)
        
        # Calculate word-level and character-level accuracies
        word_accuracy = word_level_accuracy(detected_text, ground_truth)
        char_accuracy = character_level_accuracy(detected_text, ground_truth)
        
        # Calculate Levenshtein distance (edit distance)
        lev_distance = editdistance.eval(detected_text, ground_truth)
        
        # Calculate WER and CER
        word_error = word_error_rate(ground_truth, detected_text)
        char_error = char_error_rate(ground_truth, detected_text)
        
        word_accuracies.append(word_accuracy)
        char_accuracies.append(char_accuracy)
        lev_distances.append(lev_distance)
        word_errors.append(word_error)
        char_errors.append(char_error)
    
    # Calculate overall metrics (average word and character accuracies)
    avg_word_accuracy = np.mean(word_accuracies)
    avg_char_accuracy = np.mean(char_accuracies)
    avg_lev_distance = np.mean(lev_distances)
    avg_word_error = np.mean(word_errors)
    avg_char_error = np.mean(char_errors)
    
    # Prepare final results
    final_results = f"Overall Evaluation Results:\n"
    final_results += f"Average Word Accuracy: {avg_word_accuracy:.4f}\n"
    final_results += f"Average Character Accuracy: {avg_char_accuracy:.4f}\n"
    final_results += f"Average Levenshtein Distance: {avg_lev_distance:.4f}\n"
    final_results += f"Average Word Error Rate (WER): {avg_word_error:.4f}\n"
    final_results += f"Average Character Error Rate (CER): {avg_char_error:.4f}\n"
    
    print(final_results)
    
    # Write the final evaluation results to the file
    with open(results_file, 'w') as file:
        file.write(final_results)

# Select OCR method (can be changed here)
selected_ocr_method = detect_paddleocr_text  # Change to any of the available methods
ocr_name = "PaddleOCR"  # Change to match the selected OCR method's name

# Define the results file name based on the OCR method
results_file = f'{ocr_name}_evaluation_results.txt'

# Run the evaluation
evaluate_ocr(selected_ocr_method, results_file)
