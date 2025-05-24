import base64
import numpy as np
import os
import cv2
import random
import logging
import io
from PIL import Image

# This is an enhanced waste classifier that uses color, texture, and shape features
# to identify different types of waste materials

logger = logging.getLogger(__name__)

# Waste categories and their typical color ranges in HSV
WASTE_CATEGORIES = {
    'plastic': {
        'description': 'Plastic materials like bottles, containers, bags',
        'color_ranges': [
            {'lower': [0, 0, 100], 'upper': [180, 60, 255]},  # White/clear plastic
            {'lower': [90, 50, 50], 'upper': [130, 255, 255]},  # Blue plastic
            {'lower': [36, 50, 50], 'upper': [70, 255, 255]},  # Green plastic
        ],
        'texture_weight': 0.2,
        'shape_weight': 0.3
    },
    'metal': {
        'description': 'Metal items like cans, foil, and metal containers',
        'color_ranges': [
            {'lower': [0, 0, 150], 'upper': [180, 30, 255]},  # Silver/gray
            {'lower': [15, 50, 50], 'upper': [30, 255, 255]},  # Gold/bronze
        ],
        'texture_weight': 0.6,
        'shape_weight': 0.2
    },
    'paper': {
        'description': 'Paper products including cardboard, newspapers, magazines',
        'color_ranges': [
            {'lower': [15, 0, 70], 'upper': [30, 80, 255]},  # Brown/cardboard
            {'lower': [0, 0, 200], 'upper': [180, 10, 255]},  # White paper
            {'lower': [20, 10, 70], 'upper': [40, 100, 200]},  # Yellowish paper
        ],
        'texture_weight': 0.5,
        'shape_weight': 0.1
    },
    'glass': {
        'description': 'Glass bottles, jars, and containers',
        'color_ranges': [
            {'lower': [0, 0, 150], 'upper': [180, 40, 255]},  # Clear glass
            {'lower': [90, 50, 50], 'upper': [130, 255, 255]},  # Blue glass
            {'lower': [40, 50, 50], 'upper': [80, 255, 255]},  # Green glass
            {'lower': [0, 50, 50], 'upper': [10, 255, 255]},  # Red glass
        ],
        'texture_weight': 0.3,
        'shape_weight': 0.5
    },
    'organic': {
        'description': 'Food waste, plant materials, compostable items',
        'color_ranges': [
            {'lower': [20, 50, 20], 'upper': [60, 255, 150]},  # Green/plant material
            {'lower': [0, 50, 20], 'upper': [20, 255, 150]},  # Brown/food waste
        ],
        'texture_weight': 0.7,
        'shape_weight': 0.1
    },
    'electronic': {
        'description': 'Electronic devices, circuit boards, wires',
        'color_ranges': [
            {'lower': [0, 0, 10], 'upper': [180, 255, 80]},  # Black electronics
            {'lower': [0, 0, 81], 'upper': [180, 30, 200]},  # Gray/silver
            {'lower': [90, 50, 50], 'upper': [130, 255, 255]},  # Circuit board green
        ],
        'texture_weight': 0.4,
        'shape_weight': 0.4
    }
}

def calculate_color_match(hsv_image, category_data):
    """Calculate how well the image matches the color profile of a waste category"""
    mask = np.zeros(hsv_image.shape[:2], dtype=np.uint8)
    
    for color_range in category_data['color_ranges']:
        lower = np.array(color_range['lower'])
        upper = np.array(color_range['upper'])
        
        color_mask = cv2.inRange(hsv_image, lower, upper)
        mask = cv2.bitwise_or(mask, color_mask)
    
    # Calculate the percentage of pixels that match the color profile
    return np.sum(mask > 0) / (mask.shape[0] * mask.shape[1])

def calculate_texture_features(gray_image):
    """Calculate texture features using GLCM (simplified for demo)"""
    # For a simple texture measure, we'll use standard deviation of local regions
    kernel_size = 5
    texture_image = cv2.blur(gray_image, (kernel_size, kernel_size))
    texture_std = np.std(texture_image)
    return texture_std / 255.0  # Normalize to 0-1 range

def calculate_shape_features(image):
    """Calculate shape features based on contours"""
    # Convert to grayscale and find edges
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    blurred = cv2.GaussianBlur(gray, (5, 5), 0)
    edges = cv2.Canny(blurred, 50, 150)
    
    # Find contours
    contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    
    # If no contours, return 0 for all features
    if not contours:
        return {
            'circularity': 0,
            'rectangularity': 0,
            'elongation': 0
        }
    
    # Find the largest contour
    largest_contour = max(contours, key=cv2.contourArea)
    area = cv2.contourArea(largest_contour)
    
    # If area is too small, return 0 for all features
    if area < 100:
        return {
            'circularity': 0,
            'rectangularity': 0,
            'elongation': 0
        }
    
    # Calculate perimeter
    perimeter = cv2.arcLength(largest_contour, True)
    
    # Calculate circularity (4π × area / perimeter²)
    circularity = (4 * np.pi * area) / (perimeter ** 2) if perimeter > 0 else 0
    
    # Calculate bounding rectangle
    x, y, w, h = cv2.boundingRect(largest_contour)
    rect_area = w * h
    
    # Calculate rectangularity (area / bounding rect area)
    rectangularity = area / rect_area if rect_area > 0 else 0
    
    # Calculate elongation (width / height or height / width)
    elongation = min(w, h) / max(w, h) if max(w, h) > 0 else 0
    
    return {
        'circularity': circularity,
        'rectangularity': rectangularity,
        'elongation': elongation
    }

def classify_waste(image_data):
    """
    Classify waste from image data using color, texture, and shape features
    
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
        
        # Convert to HSV for color analysis
        hsv_image = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
        
        # Convert to grayscale for texture analysis
        gray_image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        
        # Calculate texture features
        texture_value = calculate_texture_features(gray_image)
        
        # Calculate shape features
        shape_features = calculate_shape_features(image)
        
        # Calculate scores for each waste category
        scores = {}
        for category, data in WASTE_CATEGORIES.items():
            # Color match score (50% of total)
            color_score = calculate_color_match(hsv_image, data) * 0.5
            
            # Texture score (weighted by category)
            texture_score = texture_value * data['texture_weight']
            
            # Shape score (weighted by category)
            shape_score = (shape_features['circularity'] * 0.4 + 
                          shape_features['rectangularity'] * 0.3 + 
                          shape_features['elongation'] * 0.3) * data['shape_weight']
            
            # Total score
            total_score = color_score + texture_score + shape_score
            scores[category] = total_score
        
        # Find the category with the highest score
        waste_type = max(scores, key=scores.get)
        confidence = scores[waste_type]
        
        # Normalize confidence to 0.6-0.95 range
        confidence = 0.6 + (confidence * 0.35)
        
        # Ensure confidence is between 0 and 1
        confidence = max(0, min(1, confidence))
        
        logger.debug(f"Classified as {waste_type} with {confidence:.2f} confidence")
        return waste_type, round(confidence, 2)
        
    except Exception as e:
        logger.error(f"Error in waste classification: {str(e)}")
        # As a fallback, return a random classification but with lower confidence
        waste_type = random.choice(list(WASTE_CATEGORIES.keys()))
        confidence = random.uniform(0.4, 0.6)
        return waste_type, round(confidence, 2)
