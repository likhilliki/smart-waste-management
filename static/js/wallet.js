/**
 * Cryptocurrency wallet integration for token rewards
 */

// Check if MetaMask is installed
function checkMetaMaskInstalled() {
    return typeof window.ethereum !== 'undefined';
}

// Connect to MetaMask wallet
async function connectMetaMask() {
    if (!checkMetaMaskInstalled()) {
        showWalletError('MetaMask is not installed. Please install the MetaMask browser extension.');
        return null;
    }
    
    try {
        // Request account access
        const accounts = await window.ethereum.request({ method: 'eth_requestAccounts' });
        return accounts[0]; // Return the first account
    } catch (error) {
        showWalletError('Error connecting to MetaMask: ' + error.message);
        return null;
    }
}

// Sign message using MetaMask to verify wallet ownership
async function signMessage(message, account) {
    try {
        const signature = await window.ethereum.request({
            method: 'personal_sign',
            params: [message, account]
        });
        return signature;
    } catch (error) {
        showWalletError('Error signing message: ' + error.message);
        return null;
    }
}

// Verify wallet connection
async function verifyWalletConnection(walletType, walletAddress) {
    // Create a form submission with wallet details
    const formData = new FormData();
    formData.append('wallet_type', walletType);
    formData.append('wallet_address', walletAddress);
    
    try {
        const response = await fetch('/user/verify_wallet', {
            method: 'POST',
            body: formData
        });
        
        const data = await response.json();
        return data.success;
    } catch (error) {
        showWalletError('Error verifying wallet: ' + error.message);
        return false;
    }
}

// Transfer tokens to blockchain wallet
async function transferTokensToWallet(amount, walletAddress, walletType) {
    try {
        const response = await fetch('/user/transfer_tokens', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                amount: amount,
                wallet_address: walletAddress,
                wallet_type: walletType
            })
        });
        
        return await response.json();
    } catch (error) {
        showWalletError('Error transferring tokens: ' + error.message);
        return { success: false, error: error.message };
    }
}

// Show wallet error message
function showWalletError(message) {
    const errorElement = document.getElementById('wallet-error');
    if (errorElement) {
        errorElement.textContent = message;
        errorElement.classList.remove('d-none');
    } else {
        console.error('Wallet error:', message);
    }
}

// Initialize wallet functionality
document.addEventListener('DOMContentLoaded', function() {
    // MetaMask connection button
    const connectMetaMaskBtn = document.getElementById('connectMetamask');
    if (connectMetaMaskBtn) {
        connectMetaMaskBtn.addEventListener('click', async function() {
            const account = await connectMetaMask();
            if (account) {
                document.getElementById('wallet_address').value = account;
                document.getElementById('wallet_type').value = 'metamask';
                
                // Show success message
                const statusDiv = document.getElementById('metamaskStatus');
                if (statusDiv) {
                    statusDiv.innerHTML = `
                        <div class="alert alert-success">
                            <i class="fas fa-check-circle me-2"></i> Connected to ${account}
                            <br><small>Click Connect Wallet to confirm</small>
                        </div>
                    `;
                }
            }
        });
    }
    
    // Token transfer button
    const transferBtn = document.getElementById('transferTokens');
    if (transferBtn) {
        transferBtn.addEventListener('click', async function() {
            const amount = parseFloat(transferBtn.getAttribute('data-amount') || '0');
            const walletAddress = transferBtn.getAttribute('data-wallet');
            const walletType = transferBtn.getAttribute('data-wallet-type');
            
            if (!amount || !walletAddress || !walletType) {
                showWalletError('Missing required information for transfer');
                return;
            }
            
            const statusDiv = document.getElementById('transferStatus');
            if (statusDiv) {
                statusDiv.innerHTML = '<div class="alert alert-info">Initiating transfer to blockchain...</div>';
            }
            
            // Perform the transfer
            const result = await transferTokensToWallet(amount, walletAddress, walletType);
            
            if (result.success) {
                if (statusDiv) {
                    statusDiv.innerHTML = `
                        <div class="alert alert-success">
                            <i class="fas fa-check-circle me-2"></i> Transfer completed!
                            Tokens have been sent to your wallet.
                            <br><small>Transaction Hash: ${result.transaction_hash}</small>
                        </div>
                    `;
                }
            } else {
                showWalletError(result.error || 'Failed to transfer tokens');
            }
        });
    }
});