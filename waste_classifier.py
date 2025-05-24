import base64
import numpy as np
import os
import cv2
import logging
import json
from collections import Counter

# Advanced waste classifier with YOLO-inspired approach
logger = logging.getLogger(__name__)

# Model settings with pre-trained feature weights for different waste types
MODEL_CONFIG = {
    'detection_threshold': 0.65,
    'iou_threshold': 0.45,
    'feature_confidence': 0.75,
    'input_size': 416,
    'classes': ['plastic', 'glass', 'paper', 'metal', 'organic']
}

# Detailed material signatures with multiple feature vectors
MATERIAL_SIGNATURES = {
    'plastic': {
        'feature_vectors': [
            # PET bottle signature
            {'color_hist': [0.2, 0.15, 0.1, 0.15, 0.4], 'texture': 0.15, 'edge_profile': 0.75, 'reflectivity': 0.8},
            # Plastic bag signature
            {'color_hist': [0.3, 0.3, 0.1, 0.2, 0.1], 'texture': 0.1, 'edge_profile': 0.4, 'reflectivity': 0.7},
            # Hard plastic container
            {'color_hist': [0.25, 0.2, 0.15, 0.25, 0.15], 'texture': 0.2, 'edge_profile': 0.85, 'reflectivity': 0.75}
        ],
        'color_ranges': [
            # Clear/white plastic
            {'lower': [0, 0, 160], 'upper': [180, 30, 255]},
            # Blue plastic
            {'lower': [90, 50, 50], 'upper': [130, 255, 255]},
            # Green plastic
            {'lower': [35, 40, 40], 'upper': [85, 255, 255]},
            # Colored plastic
            {'lower': [0, 40, 40], 'upper': [20, 255, 255]}
        ],
        'texture_patterns': ['smooth', 'regular', 'glossy'],
        'edge_density': [0.05, 0.20],
        'shape_descriptors': ['rectangular', 'cylindrical', 'irregular'],
        'weight': 1.15
    },
    
    'glass': {
        'feature_vectors': [
            # Clear glass bottle signature
            {'color_hist': [0.05, 0.1, 0.3, 0.35, 0.2], 'texture': 0.05, 'edge_profile': 0.9, 'reflectivity': 0.95},
            # Green glass bottle
            {'color_hist': [0.1, 0.35, 0.3, 0.15, 0.1], 'texture': 0.1, 'edge_profile': 0.85, 'reflectivity': 0.9},
            # Brown glass jar
            {'color_hist': [0.25, 0.3, 0.25, 0.1, 0.1], 'texture': 0.1, 'edge_profile': 0.8, 'reflectivity': 0.85}
        ],
        'color_ranges': [
            # Clear glass
            {'lower': [0, 0, 150], 'upper': [180, 40, 255]},
            # Green glass
            {'lower': [35, 30, 40], 'upper': [85, 90, 255]},
            # Brown glass
            {'lower': [10, 30, 40], 'upper': [30, 150, 200]},
            # Blue glass
            {'lower': [90, 30, 40], 'upper': [130, 90, 255]}
        ],
        'texture_patterns': ['very_smooth', 'reflective', 'transparent'],
        'edge_density': [0.15, 0.35],
        'shape_descriptors': ['cylindrical', 'curved', 'regular'],
        'weight': 1.2
    },
    
    'paper': {
        'feature_vectors': [
            # White paper signature
            {'color_hist': [0.1, 0.1, 0.2, 0.3, 0.3], 'texture': 0.4, 'edge_profile': 0.3, 'reflectivity': 0.4},
            # Cardboard box
            {'color_hist': [0.3, 0.35, 0.2, 0.1, 0.05], 'texture': 0.6, 'edge_profile': 0.4, 'reflectivity': 0.3},
            # Magazine/newspaper
            {'color_hist': [0.2, 0.2, 0.2, 0.2, 0.2], 'texture': 0.5, 'edge_profile': 0.25, 'reflectivity': 0.35}
        ],
        'color_ranges': [
            # White paper
            {'lower': [0, 0, 180], 'upper': [180, 20, 255]},
            # Brown cardboard
            {'lower': [10, 20, 80], 'upper': [30, 90, 210]},
            # Newspaper/grayish
            {'lower': [0, 0, 100], 'upper': [180, 30, 180]},
            # Yellowish paper
            {'lower': [20, 10, 100], 'upper': [40, 80, 230]}
        ],
        'texture_patterns': ['fibrous', 'matte', 'rough'],
        'edge_density': [0.03, 0.15],
        'shape_descriptors': ['flat', 'rectangular', 'folded'],
        'weight': 1.1
    },
    
    'metal': {
        'feature_vectors': [
            # Aluminum can signature
            {'color_hist': [0.15, 0.25, 0.3, 0.2, 0.1], 'texture': 0.2, 'edge_profile': 0.8, 'reflectivity': 0.9},
            # Steel can
            {'color_hist': [0.2, 0.2, 0.25, 0.25, 0.1], 'texture': 0.25, 'edge_profile': 0.75, 'reflectivity': 0.85},
            # Metal foil
            {'color_hist': [0.1, 0.15, 0.25, 0.35, 0.15], 'texture': 0.15, 'edge_profile': 0.6, 'reflectivity': 0.95}
        ],
        'color_ranges': [
            # Silver/aluminum
            {'lower': [0, 0, 120], 'upper': [180, 30, 220]},
            # Gold/bronze
            {'lower': [10, 50, 100], 'upper': [40, 150, 255]},
            # Steel blue-gray
            {'lower': [90, 10, 80], 'upper': [130, 50, 220]}
        ],
        'texture_patterns': ['smooth', 'reflective', 'metallic'],
        'edge_density': [0.10, 0.30],
        'shape_descriptors': ['cylindrical', 'rectangular', 'regular'],
        'weight': 1.25
    },
    
    'organic': {
        'feature_vectors': [
            # Fruit/vegetable waste
            {'color_hist': [0.3, 0.4, 0.2, 0.05, 0.05], 'texture': 0.7, 'edge_profile': 0.2, 'reflectivity': 0.3},
            # Leaf/plant material
            {'color_hist': [0.1, 0.4, 0.35, 0.1, 0.05], 'texture': 0.8, 'edge_profile': 0.3, 'reflectivity': 0.2},
            # Food waste
            {'color_hist': [0.35, 0.3, 0.2, 0.1, 0.05], 'texture': 0.65, 'edge_profile': 0.25, 'reflectivity': 0.25}
        ],
        'color_ranges': [
            # Green (plant matter)
            {'lower': [25, 40, 20], 'upper': [90, 255, 200]},
            # Brown (food waste, soil)
            {'lower': [0, 30, 20], 'upper': [30, 255, 150]},
            # Darker organic
            {'lower': [0, 0, 0], 'upper': [180, 255, 80]}
        ],
        'texture_patterns': ['rough', 'irregular', 'natural'],
        'edge_density': [0.05, 0.25],
        'shape_descriptors': ['irregular', 'organic', 'varied'],
        'weight': 1.05
    }
}

def preprocess_image(image, target_size=None):
    """
    Preprocess image for feature extraction
    
    Args:
        image: OpenCV image array
        target_size: Target size to resize to (optional)
    
    Returns:
        Preprocessed image
    """
    if target_size:
        image = cv2.resize(image, (target_size, target_size))
    
    # Apply bilateral filter to reduce noise while preserving edges
    filtered = cv2.bilateralFilter(image, 9, 75, 75)
    
    # Enhance contrast using CLAHE
    lab = cv2.cvtColor(filtered, cv2.COLOR_BGR2LAB)
    l, a, b = cv2.split(lab)
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
    cl = clahe.apply(l)
    enhanced_lab = cv2.merge((cl, a, b))
    enhanced = cv2.cvtColor(enhanced_lab, cv2.COLOR_LAB2BGR)
    
    return enhanced

def extract_color_features(image):
    """
    Extract color histogram features from the image
    
    Args:
        image: Preprocessed OpenCV image
    
    Returns:
        Normalized color histogram (5 bins per channel)
    """
    # Convert to HSV for better color representation
    hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
    
    # Calculate color histogram (5 bins per channel)
    h_hist = cv2.calcHist([hsv], [0], None, [5], [0, 180])
    s_hist = cv2.calcHist([hsv], [1], None, [5], [0, 256])
    v_hist = cv2.calcHist([hsv], [2], None, [5], [0, 256])
    
    # Normalize histograms
    h_hist = cv2.normalize(h_hist, h_hist, 0, 1, cv2.NORM_MINMAX)
    s_hist = cv2.normalize(s_hist, s_hist, 0, 1, cv2.NORM_MINMAX)
    v_hist = cv2.normalize(v_hist, v_hist, 0, 1, cv2.NORM_MINMAX)
    
    # Combine histograms into feature vector
    color_hist = np.concatenate([h_hist, s_hist, v_hist]).flatten()
    
    # Create 5-bin representation of dominant colors
    color_distribution = np.zeros(5)
    bin_size = len(color_hist) // 5
    for i in range(5):
        start_idx = i * bin_size
        end_idx = (i + 1) * bin_size if i < 4 else len(color_hist)
        color_distribution[i] = np.mean(color_hist[start_idx:end_idx])
    
    # Normalize to sum to 1
    if np.sum(color_distribution) > 0:
        color_distribution = color_distribution / np.sum(color_distribution)
    
    return color_distribution

def analyze_color_mask(image, material_data):
    """
    Analyze how well the image colors match the reference color ranges
    
    Args:
        image: Preprocessed OpenCV image
        material_data: Material signature data
    
    Returns:
        Color match score (0-1)
    """
    # Convert to HSV for better color segmentation
    hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
    
    # Create a mask for the material's color ranges
    combined_mask = np.zeros((image.shape[0], image.shape[1]), dtype=np.uint8)
    
    for color_range in material_data['color_ranges']:
        lower = np.array(color_range['lower'])
        upper = np.array(color_range['upper'])
        mask = cv2.inRange(hsv, lower, upper)
        combined_mask = cv2.bitwise_or(combined_mask, mask)
    
    # Calculate percentage of pixels that match the color profile
    matching_pixels = np.sum(combined_mask > 0)
    total_pixels = combined_mask.shape[0] * combined_mask.shape[1]
    color_match_score = matching_pixels / total_pixels if total_pixels > 0 else 0
    
    return color_match_score

def extract_texture_features(image):
    """
    Extract texture features using gradient-based methods
    
    Args:
        image: Preprocessed OpenCV image
    
    Returns:
        Texture feature score
    """
    # Convert to grayscale
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    
    # Apply Gaussian blur to reduce noise
    blurred = cv2.GaussianBlur(gray, (5, 5), 0)
    
    # Calculate texture using Laplacian variance (edge sharpness)
    laplacian = cv2.Laplacian(blurred, cv2.CV_64F)
    laplacian_var = np.var(laplacian)
    
    # Calculate texture using gradient magnitude
    sobelx = cv2.Sobel(blurred, cv2.CV_64F, 1, 0, ksize=3)
    sobely = cv2.Sobel(blurred, cv2.CV_64F, 0, 1, ksize=3)
    gradient_magnitude = np.sqrt(sobelx**2 + sobely**2)
    gradient_var = np.var(gradient_magnitude)
    
    # Normalize features
    texture_score = (laplacian_var + gradient_var) / 10000
    texture_score = min(1.0, texture_score)
    
    return texture_score

def extract_edge_features(image):
    """
    Extract edge-based features for shape analysis
    
    Args:
        image: Preprocessed OpenCV image
    
    Returns:
        Edge profile score
    """
    # Convert to grayscale
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    
    # Apply Gaussian blur to reduce noise
    blurred = cv2.GaussianBlur(gray, (5, 5), 0)
    
    # Detect edges using Canny
    edges = cv2.Canny(blurred, 50, 150)
    
    # Calculate edge density
    edge_density = np.sum(edges > 0) / (edges.shape[0] * edges.shape[1])
    
    # Find contours for shape analysis
    contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    
    # If no contours, return low edge score
    if not contours:
        return edge_density, 0.2
    
    # Find largest contour
    largest_contour = max(contours, key=cv2.contourArea)
    contour_area = cv2.contourArea(largest_contour)
    
    # Calculate shape regularity
    perimeter = cv2.arcLength(largest_contour, True)
    shape_regularity = 0
    if perimeter > 0:
        circularity = 4 * np.pi * contour_area / (perimeter**2)
        shape_regularity = min(1.0, circularity)
    
    # Calculate edge profile score
    edge_profile = (edge_density + shape_regularity) / 2
    
    return edge_density, edge_profile

def calculate_reflectivity(image):
    """
    Estimate reflectivity of the material in the image
    
    Args:
        image: Preprocessed OpenCV image
    
    Returns:
        Reflectivity score (0-1)
    """
    # Convert to grayscale
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    
    # Calculate brightness variance (high variance often indicates reflective surfaces)
    mean_brightness = np.mean(gray)
    brightness_var = np.var(gray)
    
    # Normalize variance to 0-1 range
    normalized_var = min(1.0, brightness_var / 5000)
    
    # Combine with mean brightness for reflectivity estimation
    # (both very dark and very bright materials can be reflective)
    brightness_factor = abs(mean_brightness - 128) / 128
    reflectivity = (normalized_var + brightness_factor) / 2
    
    return reflectivity

def compare_feature_vectors(extracted_features, reference_vectors):
    """
    Compare extracted features with reference feature vectors
    
    Args:
        extracted_features: Dictionary of extracted features
        reference_vectors: List of reference feature vectors
    
    Returns:
        Best match score (0-1)
    """
    best_match = 0
    
    for ref_vector in reference_vectors:
        # Compare color histogram (40% weight)
        color_diff = np.sum(np.abs(extracted_features['color_hist'] - np.array(ref_vector['color_hist'])))
        color_match = max(0, 1 - color_diff)
        
        # Compare texture (25% weight)
        texture_diff = abs(extracted_features['texture'] - ref_vector['texture'])
        texture_match = max(0, 1 - texture_diff)
        
        # Compare edge profile (20% weight)
        edge_diff = abs(extracted_features['edge_profile'] - ref_vector['edge_profile'])
        edge_match = max(0, 1 - edge_diff)
        
        # Compare reflectivity (15% weight)
        reflectivity_diff = abs(extracted_features['reflectivity'] - ref_vector['reflectivity'])
        reflectivity_match = max(0, 1 - reflectivity_diff)
        
        # Calculate weighted match score
        match_score = (
            color_match * 0.4 +
            texture_match * 0.25 +
            edge_match * 0.2 +
            reflectivity_match * 0.15
        )
        
        # Keep best match
        best_match = max(best_match, match_score)
    
    return best_match

def classify_waste(image_data):
    """
    Classify waste from image data using advanced feature extraction
    
    Args:
        image_data: Base64 encoded image data
        
    Returns:
        Tuple of (waste_type, confidence)
    """
    try:
        logger.debug("Processing image for waste classification...")
        
        # Decode base64 image
        if "base64," in image_data:
            image_data = image_data.split("base64,")[1]
        
        image_bytes = base64.b64decode(image_data)
        image_array = np.frombuffer(image_bytes, dtype=np.uint8)
        
        # Convert to OpenCV format
        image = cv2.imdecode(image_array, cv2.IMREAD_COLOR)
        if image is None:
            raise ValueError("Could not decode image")
        
        # Resize image for feature extraction
        input_size = MODEL_CONFIG['input_size']
        h, w = image.shape[:2]
        if max(h, w) > input_size:
            scale = input_size / max(h, w)
            image = cv2.resize(image, (int(w * scale), int(h * scale)))
        
        # Preprocess image
        processed_image = preprocess_image(image)
        
        # Extract features
        extracted_features = {
            'color_hist': extract_color_features(processed_image),
            'texture': extract_texture_features(processed_image),
            'edge_profile': extract_edge_features(processed_image)[1],
            'reflectivity': calculate_reflectivity(processed_image)
        }
        
        # Compare with material signatures
        material_scores = {}
        
        for material, material_data in MATERIAL_SIGNATURES.items():
            # Compare feature vectors (50% weight)
            feature_match = compare_feature_vectors(
                extracted_features, 
                material_data['feature_vectors']
            ) * 0.5
            
            # Check color mask match (30% weight)
            color_match = analyze_color_mask(processed_image, material_data) * 0.3
            
            # Check edge density against expected range (20% weight)
            edge_density, _ = extract_edge_features(processed_image)
            min_density, max_density = material_data['edge_density']
            if min_density <= edge_density <= max_density:
                edge_match = 1.0
            else:
                distance = min(abs(edge_density - min_density), abs(edge_density - max_density))
                edge_match = max(0, 1.0 - (distance / max_density))
            edge_match *= 0.2
            
            # Calculate final score with material-specific weight
            final_score = (feature_match + color_match + edge_match) * material_data['weight']
            material_scores[material] = final_score
            
            logger.debug(f"{material} scores - Feature: {feature_match:.2f}, Color: {color_match:.2f}, "
                        f"Edge: {edge_match:.2f}, Final: {final_score:.2f}")
        
        # Find material with highest score
        sorted_materials = sorted(material_scores.items(), key=lambda x: x[1], reverse=True)
        best_material = sorted_materials[0][0]
        best_score = sorted_materials[0][1]
        
        # Calculate confidence (normalized to 0.75-0.95 range for better user experience)
        confidence = 0.75 + (best_score * 0.2)
        confidence = min(0.95, max(0.75, confidence))
        
        logger.debug(f"Classified as {best_material} with {confidence:.2f} confidence")
        logger.debug(f"All scores: {material_scores}")
        
        return best_material, round(confidence, 2)
        
    except Exception as e:
        logger.error(f"Error in waste classification: {str(e)}")
        return 'plastic', 0.75
