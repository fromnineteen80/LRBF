/**
 * Profile Page JavaScript
 * Handles profile updates and password changes
 * Railyard Markets - The Luggage Room Boys Fund
 */

document.addEventListener('DOMContentLoaded', function() {
    initializeProfilePage();
});

/**
 * Initialize profile page event listeners
 */
function initializeProfilePage() {
    // Profile form submission
    const profileForm = document.getElementById('profileForm');
    if (profileForm) {
        profileForm.addEventListener('submit', handleProfileUpdate);
    }
    
    // Password form submission
    const passwordForm = document.getElementById('passwordForm');
    if (passwordForm) {
        passwordForm.addEventListener('submit', handlePasswordChange);
    }
    
    // Store original values for reset functionality
    storeOriginalValues();
}

/**
 * Store original form values for reset functionality
 */
function storeOriginalValues() {
    const firstName = document.getElementById('firstName');
    const lastName = document.getElementById('lastName');
    const phone = document.getElementById('phone');
    
    if (firstName) firstName.dataset.original = firstName.value;
    if (lastName) lastName.dataset.original = lastName.value;
    if (phone) phone.dataset.original = phone.value;
}

/**
 * Reset profile form to original values
 */
function resetProfileForm() {
    const firstName = document.getElementById('firstName');
    const lastName = document.getElementById('lastName');
    const phone = document.getElementById('phone');
    
    if (firstName && firstName.dataset.original) {
        firstName.value = firstName.dataset.original;
    }
    if (lastName && lastName.dataset.original) {
        lastName.value = lastName.dataset.original;
    }
    if (phone && phone.dataset.original) {
        phone.value = phone.dataset.original;
    }
    
    showSnackbar('Changes discarded');
}

/**
 * Handle profile update form submission
 */
async function handleProfileUpdate(event) {
    event.preventDefault();
    
    const form = event.target;
    const submitButton = form.querySelector('md-filled-button[type="submit"]');
    
    // Get form data
    const formData = {
        first_name: document.getElementById('firstName').value.trim(),
        last_name: document.getElementById('lastName').value.trim(),
        phone: document.getElementById('phone').value.trim()
    };
    
    // Validate required fields
    if (!formData.first_name || !formData.last_name) {
        showSnackbar('First name and last name are required');
        return;
    }
    
    // Disable submit button during request
    if (submitButton) {
        submitButton.disabled = true;
    }
    
    try {
        // Call API to update profile
        const response = await fetch('/api/auth/update-profile', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(formData)
        });
        
        const data = await response.json();
        
        if (response.ok && data.success) {
            showSnackbar('Profile updated successfully');
            
            // Update stored original values
            storeOriginalValues();
            
            // Update any displayed name in the UI if needed
            updateDisplayedName(formData.first_name, formData.last_name);
        } else {
            showSnackbar(data.error || 'Failed to update profile');
        }
    } catch (error) {
        console.error('Profile update error:', error);
        showSnackbar('Error updating profile. Please try again.');
    } finally {
        // Re-enable submit button
        if (submitButton) {
            submitButton.disabled = false;
        }
    }
}

/**
 * Handle password change form submission
 */
async function handlePasswordChange(event) {
    event.preventDefault();
    
    const form = event.target;
    const submitButton = form.querySelector('md-filled-button[type="submit"]');
    
    // Get form data
    const currentPassword = document.getElementById('currentPassword').value;
    const newPassword = document.getElementById('newPassword').value;
    const confirmPassword = document.getElementById('confirmPassword').value;
    
    // Validate passwords match
    if (newPassword !== confirmPassword) {
        showSnackbar('New passwords do not match');
        return;
    }
    
    // Validate password strength (minimum 8 characters, at least one number and one special char)
    const passwordRegex = /^(?=.*[0-9])(?=.*[!@#$%^&*])[a-zA-Z0-9!@#$%^&*]{8,}$/;
    if (!passwordRegex.test(newPassword)) {
        showSnackbar('Password must be at least 8 characters with a number and special character');
        return;
    }
    
    // Disable submit button during request
    if (submitButton) {
        submitButton.disabled = true;
    }
    
    try {
        // Call API to change password
        const response = await fetch('/api/auth/change-password', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                current_password: currentPassword,
                new_password: newPassword
            })
        });
        
        const data = await response.json();
        
        if (response.ok && data.success) {
            showSnackbar('Password changed successfully');
            
            // Clear password fields
            document.getElementById('currentPassword').value = '';
            document.getElementById('newPassword').value = '';
            document.getElementById('confirmPassword').value = '';
        } else {
            showSnackbar(data.error || 'Failed to change password');
        }
    } catch (error) {
        console.error('Password change error:', error);
        showSnackbar('Error changing password. Please try again.');
    } finally {
        // Re-enable submit button
        if (submitButton) {
            submitButton.disabled = false;
        }
    }
}

/**
 * Update displayed name in the UI (if name appears in header/nav)
 */
function updateDisplayedName(firstName, lastName) {
    // This function can be extended if the user's name is displayed
    // elsewhere in the UI (e.g., in a user menu)
    const fullName = `${firstName} ${lastName}`;
    
    // Example: Update user menu if it exists
    const userMenuName = document.querySelector('.user-menu-name');
    if (userMenuName) {
        userMenuName.textContent = fullName;
    }
}

/**
 * Show snackbar notification
 * (Uses common.js showSnackbar function if available, otherwise fallback)
 */
function showSnackbar(message) {
    // Check if common.js showSnackbar exists
    if (typeof window.showSnackbar === 'function') {
        window.showSnackbar(message);
        return;
    }
    
    // Fallback implementation
    const snackbar = document.getElementById('snackbar');
    if (!snackbar) return;
    
    const textElement = snackbar.querySelector('.snackbar-text');
    if (textElement) {
        textElement.textContent = message;
    }
    
    snackbar.classList.add('active');
    
    setTimeout(() => {
        snackbar.classList.remove('active');
    }, 4000);
}
