/**
 * Camera handling for waste scanning
 */

let stream = null;
let capturedImage = null;

/**
 * Initialize the camera for waste scanning
 */
function initCamera(videoElement) {
    if (!videoElement) {
        console.error('Video element not found');
        return;
    }
    
    // Check if browser supports getUserMedia
    if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
        showError('Your browser does not support camera access');
        return;
    }
    
    // Access the device camera
    navigator.mediaDevices.getUserMedia({ 
        video: { 
            facingMode: 'environment', // Prefer rear camera on mobile
            width: { ideal: 1280 },
            height: { ideal: 720 }
        } 
    })
    .then(function(mediaStream) {
        stream = mediaStream;
        videoElement.srcObject = mediaStream;
        videoElement.play();
        
        // Show camera container
        const cameraContainer = document.getElementById('camera-container');
        if (cameraContainer) {
            cameraContainer.classList.remove('d-none');
        }
    })
    .catch(function(error) {
        console.error('Error accessing camera:', error);
        showError('Could not access camera: ' + error.message);
    });
}

/**
 * Stop the camera stream
 */
function stopCamera() {
    if (stream) {
        stream.getTracks().forEach(track => {
            track.stop();
        });
        stream = null;
    }
}

/**
 * Capture an image from the video stream
 */
function captureImage(videoElement, canvasElement) {
    if (!videoElement || !canvasElement) {
        console.error('Video or canvas element not found');
        return null;
    }
    
    const context = canvasElement.getContext('2d');
    
    // Set canvas dimensions to match video
    canvasElement.width = videoElement.videoWidth;
    canvasElement.height = videoElement.videoHeight;
    
    // Draw the current video frame to the canvas
    context.drawImage(videoElement, 0, 0, canvasElement.width, canvasElement.height);
    
    // Get image data as base64 string
    capturedImage = canvasElement.toDataURL('image/jpeg');
    
    // Show captured image
    const imagePreview = document.getElementById('captured-image');
    if (imagePreview) {
        imagePreview.src = capturedImage;
        imagePreview.classList.remove('d-none');
    }
    
    return capturedImage;
}

/**
 * Classify waste from the captured image
 */
function classifyWaste(imageData) {
    return new Promise((resolve, reject) => {
        if (!imageData) {
            reject(new Error('No image data'));
            return;
        }
        
        // Show loading indicator
        const loadingIndicator = document.getElementById('loading-indicator');
        if (loadingIndicator) {
            loadingIndicator.classList.remove('d-none');
        }
        
        // Send image to backend for classification
        fetch('/user/classify', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ image: imageData })
        })
        .then(response => {
            if (!response.ok) {
                throw new Error('Classification failed');
            }
            return response.json();
        })
        .then(data => {
            // Hide loading indicator
            if (loadingIndicator) {
                loadingIndicator.classList.add('d-none');
            }
            
            resolve(data);
        })
        .catch(error => {
            console.error('Error classifying waste:', error);
            
            // Hide loading indicator
            if (loadingIndicator) {
                loadingIndicator.classList.add('d-none');
            }
            
            reject(error);
        });
    });
}

/**
 * Generate QR code for the classified waste
 */
function generateWasteQR(wasteType) {
    return new Promise((resolve, reject) => {
        // Show loading indicator
        const loadingIndicator = document.getElementById('loading-indicator');
        if (loadingIndicator) {
            loadingIndicator.classList.remove('d-none');
        }
        
        // Send waste type to backend for QR generation
        fetch('/user/generate_qr', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ waste_type: wasteType })
        })
        .then(response => {
            if (!response.ok) {
                throw new Error('QR generation failed');
            }
            return response.json();
        })
        .then(data => {
            // Hide loading indicator
            if (loadingIndicator) {
                loadingIndicator.classList.add('d-none');
            }
            
            // Generate QR code using the library
            generateQRCode(data.qr_code, 'qr-container');
            
            resolve(data);
        })
        .catch(error => {
            console.error('Error generating QR:', error);
            
            // Hide loading indicator
            if (loadingIndicator) {
                loadingIndicator.classList.add('d-none');
            }
            
            reject(error);
        });
    });
}

/**
 * Show error message
 */
function showError(message) {
    const errorContainer = document.getElementById('error-container');
    if (errorContainer) {
        errorContainer.textContent = message;
        errorContainer.classList.remove('d-none');
    }
}
