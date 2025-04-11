// Web3 Configuration
let web3;
let userAccount;
let nftContract;

// Initialize Web3
async function initWeb3() {
    if (typeof window.ethereum !== 'undefined') {
        try {
            // Request account access
            await window.ethereum.request({ method: 'eth_requestAccounts' });
            web3 = new Web3(window.ethereum);
            userAccount = (await web3.eth.getAccounts())[0];
            
            // Update UI with connected account
            updateAccountDisplay(userAccount);
            
            // Listen for account changes
            window.ethereum.on('accountsChanged', function (accounts) {
                userAccount = accounts[0];
                updateAccountDisplay(userAccount);
            });
            
            // Listen for chain changes
            window.ethereum.on('chainChanged', function (chainId) {
                window.location.reload();
            });
        } catch (error) {
            console.error('User denied account access:', error);
            showToast('Please connect your wallet to continue', 'error');
        }
    } 
    // else {
    //     showToast('Please install MetaMask to use this application', 'error');
    // }
}

// Update account display in UI
function updateAccountDisplay(account) {
    const accountElements = document.querySelectorAll('.user-account');
    accountElements.forEach(element => {
        if (account) {
            element.textContent = `${account.slice(0, 6)}...${account.slice(-4)}`;
        } else {
            element.textContent = 'Connect Wallet';
        }
    });
}

// Show toast notification
function showToast(message, type = 'info') {
    const toastContainer = document.querySelector('.toast-container') || createToastContainer();
    const toast = document.createElement('div');
    toast.className = `toast align-items-center text-white bg-${type} border-0`;
    toast.setAttribute('role', 'alert');
    toast.setAttribute('aria-live', 'assertive');
    toast.setAttribute('aria-atomic', 'true');
    
    toast.innerHTML = `
        <div class="d-flex">
            <div class="toast-body">
                ${message}
            </div>
            <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast"></button>
        </div>
    `;
    
    toastContainer.appendChild(toast);
    const bsToast = new bootstrap.Toast(toast);
    bsToast.show();
    
    toast.addEventListener('hidden.bs.toast', function () {
        toast.remove();
    });
}

// Create toast container if it doesn't exist
function createToastContainer() {
    const container = document.createElement('div');
    container.className = 'toast-container';
    document.body.appendChild(container);
    return container;
}

// Show loading spinner
function showSpinner() {
    const spinner = document.createElement('div');
    spinner.className = 'spinner-overlay';
    spinner.innerHTML = `
        <div class="spinner-border text-primary" role="status">
            <span class="visually-hidden">Loading...</span>
        </div>
    `;
    document.body.appendChild(spinner);
}

// Hide loading spinner
function hideSpinner() {
    const spinner = document.querySelector('.spinner-overlay');
    if (spinner) {
        spinner.remove();
    }
}

// Copy text to clipboard
function copyToClipboard(text) {
    navigator.clipboard.writeText(text).then(() => {
        showToast('Copied to clipboard!', 'success');
    }).catch(err => {
        showToast('Failed to copy text', 'error');
    });
}

// Format number with commas and decimals
function formatNumber(number, decimals = 2) {
    return Number(number).toLocaleString('en-US', {
        minimumFractionDigits: decimals,
        maximumFractionDigits: decimals
    });
}

// Handle form submissions
document.addEventListener('DOMContentLoaded', function() {
    // Initialize Web3
    initWeb3();
    
    // Handle copy buttons
    document.querySelectorAll('.copy-btn').forEach(button => {
        button.addEventListener('click', function() {
            const textToCopy = this.getAttribute('data-copy');
            copyToClipboard(textToCopy);
        });
    });
    
    // Handle form submissions
    // document.querySelectorAll('form').forEach(form => {
    //     form.addEventListener('submit', function(e) {
    //         if (!userAccount) {
    //             e.preventDefault();
    //             showToast('Please connect your wallet first', 'error');
    //         }
    //     });
    // });
});

// Export functions for use in other files
window.initWeb3 = initWeb3;
window.showToast = showToast;
window.showSpinner = showSpinner;
window.hideSpinner = hideSpinner;
window.copyToClipboard = copyToClipboard;
window.formatNumber = formatNumber; 