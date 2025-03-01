/**
 * Streamlined CMS Tracking
 * 
 * This script handles visitor tracking and split test assignments.
 */

// Initialize tracking when the DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    // Get current page info from meta tags
    const pageId = document.querySelector('meta[name="cms-page-id"]')?.content;
    const websiteDomain = document.querySelector('meta[name="cms-website-domain"]')?.content;
    
    if (!pageId) {
        console.warn('CMS Tracking: No page ID found');
        return;
    }
    
    // Initialize tracking
    initTracking(pageId);
    
    // Check for split tests
    checkForSplitTests(pageId);
    
    // Check for conversion goals
    checkForConversionGoals();
});

/**
 * Initialize tracking for a page
 * @param {string} pageId - The ID of the page
 */
function initTracking(pageId) {
    // Record page view
    fetch('/api/page_view', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({ page_id: pageId }),
    })
    .catch(error => {
        console.error('Error recording page view:', error);
    });
}

/**
 * Check for active split tests on this page
 * @param {string} pageId - The ID of the page
 */
function checkForSplitTests(pageId) {
    // Check for content tests
    fetch(`/api/test/variant?page_id=${pageId}&test_type=content`)
        .then(response => response.json())
        .then(data => {
            if (data.active_test) {
                applySplitTestVariant(data);
            }
        })
        .catch(error => {
            console.error('Error checking for content tests:', error);
        });
}

/**
 * Apply split test variant to the page
 * @param {Object} testData - Test and variant data
 */
function applySplitTestVariant(testData) {
    // Store test data in sessionStorage for conversion tracking
    sessionStorage.setItem('cms_test_id', testData.test_id);
    sessionStorage.setItem('cms_variant_id', testData.variant_id);
    
    if (testData.test_type === 'content') {
        // Fetch content for this variant
        fetch(`/api/content_version/${testData.content_version_id}`)
            .then(response => response.json())
            .then(data => {
                applyContentChanges(data.content);
            })
            .catch(error => {
                console.error('Error applying content variant:', error);
            });
    }
}

/**
 * Apply content changes from a variant
 * @param {Object} contentChanges - Object with content changes
 */
function applyContentChanges(contentChanges) {
    // Process elements with IDs
    for (const selector in contentChanges) {
        if (selector.startsWith('#')) {
            const element = document.querySelector(selector);
            if (element) {
                element.innerHTML = contentChanges[selector];
            }
        }
    }
    
    // Process elements with classes
    for (const selector in contentChanges) {
        if (selector.startsWith('.')) {
            const elements = document.querySelectorAll(selector);
            elements.forEach(element => {
                element.innerHTML = contentChanges[selector];
            });
        }
    }
    
    // Process elements with data attributes
    for (const selector in contentChanges) {
        if (selector.startsWith('[')) {
            const elements = document.querySelectorAll(selector);
            elements.forEach(element => {
                element.innerHTML = contentChanges[selector];
            });
        }
    }
}

/**
 * Check if this page is a conversion goal
 */
function checkForConversionGoals() {
    // Get test data from session storage
    const testId = sessionStorage.getItem('cms_test_id');
    const variantId = sessionStorage.getItem('cms_variant_id');
    
    if (!testId || !variantId) {
        return;
    }
    
    // Get current page ID
    const pageId = document.querySelector('meta[name="cms-page-id"]')?.content;
    
    if (!pageId) {
        return;
    }
    
    // Check if this page is the goal page for the stored test
    fetch(`/api/test/${testId}`)
        .then(response => response.json())
        .then(data => {
            if (data.goal_page_id == pageId) {
                recordConversion(testId, variantId);
            }
        })
        .catch(error => {
            console.error('Error checking conversion goal:', error);
        });
}

/**
 * Record a conversion
 * @param {string} testId - The ID of the test
 * @param {string} variantId - The ID of the variant
 */
function recordConversion(testId, variantId) {
    fetch('/api/test/conversion', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            test_id: testId,
            variant_id: variantId
        }),
    })
    .then(() => {
        // Clear test data to prevent duplicate conversions
        sessionStorage.removeItem('cms_test_id');
        sessionStorage.removeItem('cms_variant_id');
    })
    .catch(error => {
        console.error('Error recording conversion:', error);
    });
}

/**
 * Add tracking script to a page
 * @param {string} pageId - The ID of the page
 * @param {string} domain - The domain of the website
 */
function addTrackingToPage(pageId, domain) {
    // Add meta tags for tracking
    const metaTags = `
        <meta name="cms-page-id" content="${pageId}">
        <meta name="cms-website-domain" content="${domain}">
    `;
    
    document.head.insertAdjacentHTML('beforeend', metaTags);
    
    // Add tracking script
    const script = document.createElement('script');
    script.src = '/static/js/tracking.js';
    document.head.appendChild(script);
}

// Export functions for testing
if (typeof module !== 'undefined' && module.exports) {
    module.exports = {
        initTracking,
        checkForSplitTests,
        applySplitTestVariant,
        applyContentChanges,
        checkForConversionGoals,
        recordConversion,
        addTrackingToPage
    };
}
