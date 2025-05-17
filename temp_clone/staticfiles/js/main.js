// Main JavaScript for Scooter Rental Management System

document.addEventListener('DOMContentLoaded', function() {
    // Add Bootstrap classes to form elements
    applyBootstrapClasses();
    
    // Setup automatic fade-out for alerts
    setupAlertDismissal();
    
    // Initialize any tooltips
    initializeTooltips();
    
    // Initialize any popovers
    initializePopovers();
    
    // Setup event listeners for forms
    setupFormValidation();
    
    // Setup dynamic content loading where needed
    setupDynamicContent();
    
    // Check for alerts count and update badge
    updateAlertCount();
});

/**
 * Apply Bootstrap classes to form elements
 */
function applyBootstrapClasses() {
    // Add form-control class to inputs, textareas and selects
    document.querySelectorAll('input:not([type="checkbox"]):not([type="radio"]):not([type="hidden"]):not(.form-control), textarea:not(.form-control), select:not(.form-select)').forEach(function(element) {
        if (element.tagName === 'SELECT') {
            element.classList.add('form-select');
        } else {
            element.classList.add('form-control');
        }
    });
    
    // Add form-check-input to checkboxes and radios
    document.querySelectorAll('input[type="checkbox"]:not(.form-check-input), input[type="radio"]:not(.form-check-input)').forEach(function(element) {
        element.classList.add('form-check-input');
    });
    
    // Make sure date/time inputs have form-control
    document.querySelectorAll('input[type="date"], input[type="datetime-local"]').forEach(function(element) {
        element.classList.add('form-control');
    });
}

/**
 * Setup automatic dismissal of alerts after 5 seconds
 */
function setupAlertDismissal() {
    document.querySelectorAll('.alert:not(.alert-permanent)').forEach(function(alert) {
        setTimeout(function() {
            // Create and dispatch a click event on the close button
            const closeButton = alert.querySelector('.btn-close');
            if (closeButton) {
                closeButton.click();
            } else {
                // If no close button, fade out the alert manually
                alert.style.transition = 'opacity 0.5s';
                alert.style.opacity = '0';
                setTimeout(function() {
                    if (alert.parentNode) {
                        alert.parentNode.removeChild(alert);
                    }
                }, 500);
            }
        }, 5000);
    });
}

/**
 * Initialize Bootstrap tooltips
 */
function initializeTooltips() {
    const tooltipTriggerList = document.querySelectorAll('[data-bs-toggle="tooltip"]');
    const tooltipList = [...tooltipTriggerList].map(tooltipTriggerEl => {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });
}

/**
 * Initialize Bootstrap popovers
 */
function initializePopovers() {
    const popoverTriggerList = document.querySelectorAll('[data-bs-toggle="popover"]');
    const popoverList = [...popoverTriggerList].map(popoverTriggerEl => {
        return new bootstrap.Popover(popoverTriggerEl);
    });
}

/**
 * Setup form validation
 */
function setupFormValidation() {
    // Get all forms that need validation
    const forms = document.querySelectorAll('.needs-validation');
    
    // Loop over them and prevent submission if invalid
    Array.from(forms).forEach(form => {
        form.addEventListener('submit', event => {
            if (!form.checkValidity()) {
                event.preventDefault();
                event.stopPropagation();
            }
            
            form.classList.add('was-validated');
        }, false);
    });
    
    // Setup automatic calculation of totals in job card forms
    setupJobCardCalculations();
    
    // Setup payment method type toggle
    setupPaymentMethodToggle();
}

/**
 * Setup job card calculations for labor and parts
 */
function setupJobCardCalculations() {
    // Total price calculation for job card parts
    document.querySelectorAll('.part-form').forEach(function(form) {
        const quantityInput = form.querySelector('input[name$="-quantity"]');
        const unitPriceInput = form.querySelector('input[name$="-unit_price"]');
        const totalPriceInput = form.querySelector('input[name$="-total_price"]');
        
        if (quantityInput && unitPriceInput && totalPriceInput) {
            const calculateTotal = function() {
                const quantity = parseFloat(quantityInput.value) || 0;
                const unitPrice = parseFloat(unitPriceInput.value) || 0;
                totalPriceInput.value = (quantity * unitPrice).toFixed(2);
            };
            
            quantityInput.addEventListener('input', calculateTotal);
            unitPriceInput.addEventListener('input', calculateTotal);
        }
    });
    
    // Labor cost calculation
    const laborHoursInput = document.querySelector('input[name="labor_hours"]');
    const laborRateInput = document.querySelector('input[name="labor_rate"]');
    const totalCostInput = document.querySelector('input[name="total_cost"]');
    
    if (laborHoursInput && laborRateInput && totalCostInput) {
        const updateTotalCost = function() {
            // This is just a placeholder. In reality, we'd need to sum up the parts costs too
            const hours = parseFloat(laborHoursInput.value) || 0;
            const rate = parseFloat(laborRateInput.value) || 0;
            const laborCost = hours * rate;
            
            // We'd need to add parts costs here in a real implementation
            totalCostInput.value = laborCost.toFixed(2);
        };
        
        laborHoursInput.addEventListener('input', updateTotalCost);
        laborRateInput.addEventListener('input', updateTotalCost);
    }
}

/**
 * Setup payment method type toggle
 */
function setupPaymentMethodToggle() {
    const paymentTypeSelect = document.querySelector('select[name="payment_type"]');
    const cardDetails = document.querySelector('.card-details');
    
    if (paymentTypeSelect && cardDetails) {
        const toggleCardDetails = function() {
            const paymentType = paymentTypeSelect.value;
            if (paymentType === 'credit_card' || paymentType === 'debit_card') {
                cardDetails.style.display = 'block';
            } else {
                cardDetails.style.display = 'none';
            }
        };
        
        // Initial state
        toggleCardDetails();
        
        // On change
        paymentTypeSelect.addEventListener('change', toggleCardDetails);
    }
}

/**
 * Setup dynamic content loading
 */
function setupDynamicContent() {
    // This would be used to implement any AJAX functionality
    // For example, loading scooter rates when a scooter is selected in rental form
    const scooterSelect = document.querySelector('select[name="scooter"]');
    const rateTypeSelect = document.querySelector('select[name="rate_type"]');
    const rateAmountInput = document.querySelector('input[name="rate_amount"]');
    
    if (scooterSelect && rateTypeSelect && rateAmountInput) {
        const updateRate = function() {
            const scooterId = scooterSelect.value;
            const rateType = rateTypeSelect.value;
            
            if (scooterId && rateType) {
                // In a real implementation, we would fetch the rate via AJAX
                console.log(`Would fetch rate for scooter ${scooterId} with type ${rateType}`);
                
                // Since we can't do real AJAX here, we'll simulate it
                // In production, this would be a fetch() call to an API endpoint
            }
        };
        
        scooterSelect.addEventListener('change', updateRate);
        rateTypeSelect.addEventListener('change', updateRate);
    }
}

/**
 * Update the alert count badge in the sidebar
 */
function updateAlertCount() {
    const alertCountBadge = document.getElementById('alertCountBadge');
    if (alertCountBadge) {
        // In a real implementation, we would fetch the count via AJAX
        // For now, we'll make an API call to get the actual count
        fetch('/analytics/alerts/count/')
            .then(response => {
                if (response.ok) {
                    return response.json();
                }
                // If there's an error or the endpoint doesn't exist, we'll just use '!' as the indicator
                throw new Error('Failed to fetch alert count');
            })
            .then(data => {
                // Update the badge with the count
                if (data && data.count > 0) {
                    alertCountBadge.textContent = data.count;
                    // Make sure the badge is visible
                    alertCountBadge.parentElement.style.display = 'inline-block';
                } else {
                    // Hide the badge if there are no alerts
                    alertCountBadge.parentElement.style.display = 'none';
                }
            })
            .catch(error => {
                console.log('Error fetching alert count:', error);
                // Make sure the badge shows something to indicate there might be alerts
                alertCountBadge.textContent = '!';
            });
    }
    
    // Set up a periodic check (every 5 minutes)
    setTimeout(updateAlertCount, 5 * 60 * 1000);
}
