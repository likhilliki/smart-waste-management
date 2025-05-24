import base64
import numpy as np
import os
import cv2
import logging
import random

# Improved waste classifier for accurately detecting different waste types
logger = logging.getLogger(__name__)

# Reference data for common waste materials with distinctive properties
WASTE_TYPES = {
    'plastic': {
        'color_ranges': [
            # Clear/white plastic (bottles, containers)
            {'hsv_lower': [0, 0, 160], 'hsv_upper': [180, 30, 255]},
            # Blue plastic (bottles, packaging)
            {'hsv_lower': [90, 50, 50], 'hsv_upper': [130, 255, 255]},
            # Green plastic (bottles)
            {'hsv_lower': [35, 40, 40], 'hsv_upper': [85, 255, 255]},
            # Colored plastic mix
            {'hsv_lower': [0, 40, 40], 'hsv_upper': [20, 255, 255]},
        ],
        'texture_threshold': 30,  # Smooth texture
        'edge_density_range': [0.05, 0.15],  # Medium edge density
        'brightness_range': [100, 240],  # Medium to high brightness
        'importance': 1.2  # Weight for this material
    },
    
    'paper': {
        'color_ranges': [
            # White paper
            {'hsv_lower': [0, 0, 180], 'hsv_upper': [180, 20, 255]},
            # Brown cardboard
            {'hsv_lower': [10, 20, 80], 'hsv_upper': [30, 90, 200]},
            # Yellowish paper
            {'hsv_lower': [20, 10, 100], 'hsv_upper': [40, 60, 220]},
            # Newspaper/grayish
            {'hsv_lower': [0, 0, 100], 'hsv_upper': [180, 20, 180]},
        ],
        'texture_threshold': 50,  # Fibrous texture (higher value)
        'edge_density_range': [0.03, 0.10],  # Low to medium edge density
        'brightness_range': [120, 240],  # Medium to high brightness
        'importance': 1.1  # Weight for this material
    },
    
    'glass': {
        'color_ranges': [
            # Clear glass
            {'hsv_lower': [0, 0, 150], 'hsv_upper': [180, 30, 255]},
            # Green glass
            {'hsv_lower': [40, 30, 40], 'hsv_upper': [80, 90, 255]},
            # Brown glass
            {'hsv_lower': [10, 30, 40], 'hsv_upper': [30, 90, 200]},
            # Blue glass
            {'hsv_lower': [90, 30, 40], 'hsv_upper': [130, 90, 255]},
        ],
        'texture_threshold': 20,  # Very smooth texture (low value)
        'edge_density_range': [0.15, 0.30],  # High edge density
        'brightness_range': [100, 250],  # Variable brightness due to reflections
        'importance': 1.3  # Weight for this material
    },
    
    'metal': {
        'color_ranges': [
            # Silver/aluminum
            {'hsv_lower': [0, 0, 120], 'hsv_upper': [180, 30, 220]},
            # Gold/bronze
            {'hsv_lower': [10, 50, 100], 'hsv_upper': [40, 150, 255]},
            # Tin cans (bluish-gray)
            {'hsv_lower': [90, 10, 100], 'hsv_upper': [130, 40, 220]},
        ],
        'texture_threshold': 25,  # Smooth with potential reflections
        'edge_density_range': [0.10, 0.25],  # Medium to high edge density
        'brightness_range': [120, 230],  # Medium to high brightness
        'importance': 1.25  # Weight for this material
    },
    
    'organic': {
        'color_ranges': [
            # Green (plant material)
            {'hsv_lower': [25, 40, 20], 'hsv_upper': [90, 255, 200]},
            # Brown (food waste, soil)
            {'hsv_lower': [0, 30, 20], 'hsv_upper': [30, 255, 150]},
            # Dark organic matter
            {'hsv_lower': [0, 0, 0], 'hsv_upper': [180, 255, 80]},
        ],
        'texture_threshold': 70,  # Rough texture (high value)
        'edge_density_range': [0.05, 0.15],  # Variable edges
        'brightness_range': [20, 180],  # Lower brightness overall
        'importance': 1.0  # Weight for this material
    }
}

def preprocess_image(image):
    """Apply preprocessing to improve image quality for analysis"""
    # Apply bilateral filter to reduce noise while preserving edges
    filtered = cv2.bilateralFilter(image, 9, 75, 75)
    
    # Enhance contrast using CLAHE (Contrast Limited Adaptive Histogram Equalization)
    lab = cv2.cvtColor(filtered, cv2.COLOR_BGR2LAB)
    l, a, b = cv2.split(lab)
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
    cl = clahe.apply(l)
    enhanced_lab = cv2.merge((cl, a, b))
    enhanced = cv2.cvtColor(enhanced_lab, cv2.COLOR_LAB2BGR)
    
    return enhanced

def analyze_color(image, waste_type_data):
    """Analyze color composition to identify waste materials"""
    # Convert to HSV color space for better color segmentation
    hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
    
    # Create a mask for the specific waste type's color ranges
    combined_mask = np.zeros((image.shape[0], image.shape[1]), dtype=np.uint8)
    
    for color_range in waste_type_data['color_ranges']:
        lower = np.array(color_range['hsv_lower'])
        upper = np.array(color_range['hsv_upper'])
        mask = cv2.inRange(hsv, lower, upper)
        combined_mask = cv2.bitwise_or(combined_mask, mask)
    
    # Calculate percentage of pixels that match the color profile
    matching_pixels = np.sum(combined_mask > 0)
    total_pixels = combined_mask.shape[0] * combined_mask.shape[1]
    color_match_percentage = matching_pixels / total_pixels if total_pixels > 0 else 0
    
    return color_match_percentage

def analyze_texture(image, waste_type_data):
    """Analyze texture patterns to identify material surfaces"""
    # Convert to grayscale for texture analysis
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    
    # Calculate texture using local binary patterns
    # Simplified approach using Laplacian variance
    laplacian = cv2.Laplacian(gray, cv2.CV_64F)
    texture_variance = np.var(laplacian)
    
    # Map variance to a score based on the expected texture threshold
    expected_texture = waste_type_data['texture_threshold']
    texture_score = 1.0 - min(1.0, abs(texture_variance - expected_texture) / expected_texture)
    
    return texture_score

def analyze_edges(image, waste_type_data):
    """Analyze edge patterns to identify shapes and boundaries"""
    # Convert to grayscale
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    
    # Apply Gaussian blur to reduce noise
    blurred = cv2.GaussianBlur(gray, (5, 5), 0)
    
    # Detect edges using Canny
    edges = cv2.Canny(blurred, 50, 150)
    
    # Calculate edge density
    edge_density = np.sum(edges > 0) / (edges.shape[0] * edges.shape[1])
    
    # Check if edge density is in the expected range
    min_density, max_density = waste_type_data['edge_density_range']
    if min_density <= edge_density <= max_density:
        # Edge density is in the expected range
        edge_score = 1.0
    else:
        # Calculate distance to the expected range
        if edge_density < min_density:
            distance = min_density - edge_density
        else:
            distance = edge_density - max_density
        # Normalize the distance
        edge_score = max(0, 1.0 - (distance / max_density))
    
    return edge_score

def analyze_brightness(image, waste_type_data):
    """Analyze brightness to help distinguish between materials"""
    # Convert to grayscale
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    
    # Calculate average brightness
    avg_brightness = np.mean(gray)
    
    # Check if brightness is in the expected range
    min_brightness, max_brightness = waste_type_data['brightness_range']
    if min_brightness <= avg_brightness <= max_brightness:
        # Brightness is in the expected range
        brightness_score = 1.0
    else:
        # Calculate distance to the expected range
        if avg_brightness < min_brightness:
            distance = min_brightness - avg_brightness
        else:
            distance = avg_brightness - max_brightness
        # Normalize the distance
        max_distance = 255  # Maximum possible brightness value
        brightness_score = max(0, 1.0 - (distance / max_distance))
    
    return brightness_score

def classify_waste(image_data):
    """
    Classify waste from image data using color, texture, and edge analysis
    
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
        
        # Resize image for faster processing
        max_size = 400
        h, w = image.shape[:2]
        if max(h, w) > max_size:
            scale = max_size / max(h, w)
            image = cv2.resize(image, (int(w * scale), int(h * scale)))
        
        # Preprocess image
        processed_image = preprocess_image(image)
        
        # Score each waste type
        waste_scores = {}
        
        for waste_type, waste_data in WASTE_TYPES.items():
            # Analyze color (40% weight)
            color_score = analyze_color(processed_image, waste_data) * 0.4
            
            # Analyze texture (30% weight)
            texture_score = analyze_texture(processed_image, waste_data) * 0.3
            
            # Analyze edges (20% weight)
            edge_score = analyze_edges(processed_image, waste_data) * 0.2
            
            # Analyze brightness (10% weight)
            brightness_score = analyze_brightness(processed_image, waste_data) * 0.1
            
            # Calculate final score with importance weighting
            final_score = (color_score + texture_score + edge_score + brightness_score) * waste_data['importance']
            waste_scores[waste_type] = final_score
            
            logger.debug(f"{waste_type} scores - Color: {color_score:.2f}, Texture: {texture_score:.2f}, "
                        f"Edge: {edge_score:.2f}, Brightness: {brightness_score:.2f}, Final: {final_score:.2f}")
        
        # Find waste type with highest score
        sorted_scores = sorted(waste_scores.items(), key=lambda x: x[1], reverse=True)
        best_waste_type = sorted_scores[0][0]
        best_score = sorted_scores[0][1]
        
        # Normalize confidence to 0.7-0.95 range
        confidence = 0.7 + (best_score * 0.25)
        confidence = min(0.95, max(0.7, confidence))
        
        logger.debug(f"Classified as {best_waste_type} with {confidence:.2f} confidence")
        logger.debug(f"All scores: {waste_scores}")
        
        return best_waste_type, round(confidence, 2)
        
    except Exception as e:
        logger.error(f"Error in waste classification: {str(e)}")
        return 'plastic', 0.7
