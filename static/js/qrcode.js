/**
 * QR code scanning functionality for recyclers
 */

let scanner = null;

/**
 * Initialize QR code scanner
 */
function initQRScanner(videoElement, scanResultCallback) {
    if (!videoElement) {
        console.error('Video element not found');
        return;
    }
    
    // Check if browser supports getUserMedia
    if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
        showError('Your browser does not support camera access');
        return;
    }
    
    // Create scanner instance
    scanner = new Html5QrcodeScanner(
        "qr-reader", 
        { 
            fps: 10,
            qrbox: 250
        }
    );
    
    // Start scanning
    scanner.render((qrCodeMessage) => {
        // Stop scanner after successful scan
        scanner.clear();
        
        // Call the callback with the QR code content
        if (scanResultCallback) {
            scanResultCallback(qrCodeMessage);
        }
    }, (error) => {
        // Handle scan error (usually ignored as it's just a frame without QR)
        console.log(error);
    });
}

/**
 * Verify QR code with the backend
 */
function verifyQRCode(qrCode) {
    return new Promise((resolve, reject) => {
        if (!qrCode) {
            reject(new Error('No QR code provided'));
            return;
        }
        
        // Show loading indicator
        const loadingIndicator = document.getElementById('loading-indicator');
        if (loadingIndicator) {
            loadingIndicator.classList.remove('d-none');
        }
        
        // Send QR code to backend for verification
        fetch('/recycler/verify_qr', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ qr_code: qrCode })
        })
        .then(response => {
            // Hide loading indicator
            if (loadingIndicator) {
                loadingIndicator.classList.add('d-none');
            }
            
            if (!response.ok) {
                return response.json().then(data => {
                    throw new Error(data.error || 'Verification failed');
                });
            }
            return response.json();
        })
        .then(data => {
            resolve(data);
        })
        .catch(error => {
            console.error('Error verifying QR code:', error);
            reject(error);
        });
    });
}

/**
 * Stop QR scanner
 */
function stopQRScanner() {
    if (scanner) {
        scanner.clear();
        scanner = null;
    }
}

/**
 * Show scan result
 */
function showScanResult(result, elementId) {
    const element = document.getElementById(elementId);
    if (!element) return;
    
    // Create result card
    const card = document.createElement('div');
    card.className = 'card border-success mb-3';
    
    const cardHeader = document.createElement('div');
    cardHeader.className = 'card-header bg-success text-white';
    cardHeader.textContent = 'Waste Item Verified';
    
    const cardBody = document.createElement('div');
    cardBody.className = 'card-body';
    
    // Fill card body with result details
    cardBody.innerHTML = `
        <h5 class="card-title">Successfully Processed</h5>
        <p class="card-text">
            <strong>Waste Type:</strong> ${result.waste_type}<br>
            <strong>Credits Awarded:</strong> ${result.credits_awarded} RC<br>
            <strong>User ID:</strong> ${result.user_id}
        </p>
        <div class="d-grid gap-2">
            <button class="btn btn-primary" onclick="window.location.reload()">Scan Another</button>
            <button class="btn btn-secondary" onclick="window.location.href='/recycler/dashboard'">Back to Dashboard</button>
        </div>
    `;
    
    // Assemble card
    card.appendChild(cardHeader);
    card.appendChild(cardBody);
    
    // Clear and add to container
    element.innerHTML = '';
    element.appendChild(card);
    element.classList.remove('d-none');
}

/**
 * Show error message
 */
function showScanError(message, elementId) {
    const element = document.getElementById(elementId);
    if (!element) return;
    
    // Create error card
    const card = document.createElement('div');
    card.className = 'card border-danger mb-3';
    
    const cardHeader = document.createElement('div');
    cardHeader.className = 'card-header bg-danger text-white';
    cardHeader.textContent = 'Error';
    
    const cardBody = document.createElement('div');
    cardBody.className = 'card-body';
    
    // Fill card body with error details
    cardBody.innerHTML = `
        <h5 class="card-title">Verification Failed</h5>
        <p class="card-text">${message}</p>
        <div class="d-grid gap-2">
            <button class="btn btn-primary" onclick="window.location.reload()">Try Again</button>
            <button class="btn btn-secondary" onclick="window.location.href='/recycler/dashboard'">Back to Dashboard</button>
        </div>
    `;
    
    // Assemble card
    card.appendChild(cardHeader);
    card.appendChild(cardBody);
    
    // Clear and add to container
    element.innerHTML = '';
    element.appendChild(card);
    element.classList.remove('d-none');
}
