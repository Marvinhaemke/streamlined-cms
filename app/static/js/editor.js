/**
 * Streamlined CMS Editor
 * 
 * This script enables in-place editing of content when a user is logged in.
 * It identifies editable elements on the page and makes them editable with a WYSIWYG interface.
 */

// Initialize the editor when the DOM is fully loaded
document.addEventListener('DOMContentLoaded', function() {
    const pageId = document.currentScript.getAttribute('data-page-id');
    
    if (!pageId) {
        console.error('Editor initialization failed: No page ID provided');
        return;
    }
    
    initEditor(pageId);
});

/**
 * Initialize the editor for a page
 * @param {string} pageId - The ID of the page being edited
 */
function initEditor(pageId) {
    // Create editor toolbar
    createEditorToolbar();
    
    // Fetch current content data
    fetchContentData(pageId)
        .then(data => {
            // Find and make elements editable
            makeElementsEditable(data.content);
            
            // Setup save button
            setupSaveButton(pageId);
        })
        .catch(error => {
            console.error('Failed to initialize editor:', error);
        });
}

/**
 * Create the editor toolbar
 */
function createEditorToolbar() {
    const toolbar = document.createElement('div');
    toolbar.id = 'cms-editor-toolbar';
    toolbar.innerHTML = `
        <div class="cms-editor-toolbar-inner">
            <div class="cms-editor-title">Streamlined CMS Editor</div>
            <button id="cms-save-button" class="cms-button cms-save-button">Save Changes</button>
            <button id="cms-cancel-button" class="cms-button cms-cancel-button">Cancel</button>
        </div>
    `;
    
    // Add toolbar styles
    const styles = document.createElement('style');
    styles.textContent = `
        #cms-editor-toolbar {
            position: fixed;
            top: 0;
            left: 0;
            right: 0;
            background-color: #333;
            color: white;
            z-index: 10000;
            padding: 10px;
            font-family: Arial, sans-serif;
        }
        
        .cms-editor-toolbar-inner {
            display: flex;
            align-items: center;
            max-width: 1200px;
            margin: 0 auto;
        }
        
        .cms-editor-title {
            font-size: 16px;
            font-weight: bold;
            margin-right: auto;
        }
        
        .cms-button {
            padding: 8px 16px;
            border: none;
            border-radius: 4px;
            margin-left: 10px;
            cursor: pointer;
            font-weight: bold;
        }
        
        .cms-save-button {
            background-color: #4CAF50;
            color: white;
        }
        
        .cms-cancel-button {
            background-color: #f44336;
            color: white;
        }
        
        .cms-editable {
            outline: 2px dashed #4CAF50;
            padding: 2px;
            position: relative;
        }
        
        .cms-editable:hover {
            outline: 2px solid #4CAF50;
        }
        
        body {
            margin-top: 50px;
        }
    `;
    
    document.head.appendChild(styles);
    document.body.prepend(toolbar);
    
    // Setup cancel button
    document.getElementById('cms-cancel-button').addEventListener('click', function() {
        if (confirm('Are you sure you want to cancel? All changes will be lost.')) {
            window.location.reload();
        }
    });
}

/**
 * Fetch content data from the server
 * @param {string} pageId - The ID of the page
 * @returns {Promise<Object>} - Content data object
 */
function fetchContentData(pageId) {
    return fetch(`/api/page/${pageId}/content`)
        .then(response => {
            if (!response.ok) {
                throw new Error('Failed to fetch content data');
            }
            return response.json();
        });
}

/**
 * Find elements on the page and make them editable
 * @param {Object} contentData - Content data from the server
 */
function makeElementsEditable(contentData) {
    const editableElements = new Map();
    
    // Process elements with IDs
    for (const selector in contentData) {
        if (selector.startsWith('#')) {
            const element = document.querySelector(selector);
            if (element) {
                makeElementEditable(element, selector);
                editableElements.set(selector, element);
            }
        }
    }
    
    // Process elements with classes
    for (const selector in contentData) {
        if (selector.startsWith('.')) {
            const elements = document.querySelectorAll(selector);
            elements.forEach(element => {
                // Skip if already made editable via ID
                for (const [existingSelector, existingElement] of editableElements.entries()) {
                    if (existingElement === element) {
                        return;
                    }
                }
                
                makeElementEditable(element, selector);
                editableElements.set(`${selector}-${editableElements.size}`, element);
            });
        }
    }
    
    // Process elements with data attributes
    for (const selector in contentData) {
        if (selector.startsWith('[')) {
            const elements = document.querySelectorAll(selector);
            elements.forEach(element => {
                // Skip if already made editable
                for (const [existingSelector, existingElement] of editableElements.entries()) {
                    if (existingElement === element) {
                        return;
                    }
                }
                
                makeElementEditable(element, selector);
                editableElements.set(`${selector}-${editableElements.size}`, element);
            });
        }
    }
}

/**
 * Make a single element editable
 * @param {Element} element - The DOM element to make editable
 * @param {string} selector - The CSS selector for the element
 */
function makeElementEditable(element, selector) {
    element.contentEditable = true;
    element.classList.add('cms-editable');
    element.dataset.cmsSelector = selector;
    
    // Prevent form submission when editing inside forms
    element.addEventListener('keydown', function(e) {
        if (e.key === 'Enter' && element.tagName !== 'TEXTAREA' && 
            !element.classList.contains('allow-return')) {
            e.preventDefault();
        }
    });
}

/**
 * Setup the save button functionality
 * @param {string} pageId - The ID of the page being edited
 */
function setupSaveButton(pageId) {
    document.getElementById('cms-save-button').addEventListener('click', function() {
        // Gather all content changes
        const contentChanges = {};
        const editableElements = document.querySelectorAll('.cms-editable');
        
        editableElements.forEach(element => {
            const selector = element.dataset.cmsSelector;
            if (selector) {
                contentChanges[selector] = element.innerHTML;
            }
        });
        
        // Send changes to server
        saveContentChanges(pageId, contentChanges);
    });
}

/**
 * Save content changes to the server
 * @param {string} pageId - The ID of the page
 * @param {Object} contentChanges - Object containing content changes
 */
function saveContentChanges(pageId, contentChanges) {
    const saveBtn = document.getElementById('cms-save-button');
    saveBtn.textContent = 'Saving...';
    saveBtn.disabled = true;
    
    fetch(`/api/page/${pageId}/content`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({ content: contentChanges }),
    })
    .then(response => {
        if (!response.ok) {
            throw new Error('Failed to save content');
        }
        return response.json();
    })
    .then(data => {
        saveBtn.textContent = 'Saved!';
        setTimeout(() => {
            saveBtn.textContent = 'Save Changes';
            saveBtn.disabled = false;
        }, 2000);
        
        // Flash outline to indicate saved elements
        const editableElements = document.querySelectorAll('.cms-editable');
        editableElements.forEach(element => {
            element.style.outline = '2px solid #2196F3';
            setTimeout(() => {
                element.style.outline = '';
            }, 1000);
        });
    })
    .catch(error => {
        console.error('Error saving content:', error);
        saveBtn.textContent = 'Error Saving';
        saveBtn.classList.add('cms-button-error');
        
        setTimeout(() => {
            saveBtn.textContent = 'Try Again';
            saveBtn.disabled = false;
            saveBtn.classList.remove('cms-button-error');
        }, 2000);
    });
}
