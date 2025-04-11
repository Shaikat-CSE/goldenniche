// Dashboard JavaScript
document.addEventListener('DOMContentLoaded', function() {
    // Sidebar Toggle for Mobile
    const sidebarToggle = document.getElementById('sidebar-toggle');
    const sidebar = document.querySelector('.sidebar');
    
    if (sidebarToggle) {
        sidebarToggle.addEventListener('click', function() {
            sidebar.classList.toggle('active');
        });
    }
    
    // Dropdown Toggles in Sidebar
    const dropdownToggles = document.querySelectorAll('.dropdown-toggle');
    
    dropdownToggles.forEach(function(toggle) {
        toggle.addEventListener('click', function(e) {
            e.preventDefault();
            const parent = this.parentElement;
            
            // Close other open dropdowns
            dropdownToggles.forEach(function(otherToggle) {
                if (otherToggle !== toggle) {
                    otherToggle.parentElement.classList.remove('active');
                }
            });
            
            parent.classList.toggle('active');
        });
    });
    
    // Initialize DataTables
    const tables = document.querySelectorAll('.datatable');
    
    if ($.fn.DataTable) {
        tables.forEach(function(table) {
            // Check if DataTable is already initialized on this table
            if (!$.fn.DataTable.isDataTable(table)) {
                try {
                    // Completely disable auto-detection of columns
                    $.fn.dataTable.ext.errMode = 'throw';
                    
                    // Get actual column count
                    const headerColumns = $(table).find('thead th').length;
                    const bodyColumns = $(table).find('tbody tr:first td').length || headerColumns;
                    
                    console.log('Table ID:', table.id, 'Header columns:', headerColumns, 'Body columns:', bodyColumns);
                    
                    // If there's a mismatch, adjust the table structure
                    if (headerColumns !== bodyColumns && bodyColumns > 0) {
                        if (headerColumns > bodyColumns) {
                            // Add missing columns to each row
                            $(table).find('tbody tr').each(function() {
                                for (let i = 0; i < headerColumns - bodyColumns; i++) {
                                    $(this).append('<td></td>');
                                }
                            });
                        } else {
                            // Add missing header columns
                            for (let i = 0; i < bodyColumns - headerColumns; i++) {
                                $(table).find('thead tr').append('<th></th>');
                            }
                        }
                    }
                    
                    // Now initialize DataTable with a simpler configuration
                    $(table).DataTable({
                        responsive: true,
                        paging: false,
                        ordering: true,
                        info: false,
                        searching: false,
                        autoWidth: false
                    });
                    
                    console.log('DataTable initialized successfully for table ID:', table.id);
                } catch (error) {
                    console.error('Error initializing DataTable:', error);
                    
                    // Fallback: remove datatable class to prevent further initialization attempts
                    $(table).removeClass('datatable');
                }
            }
        });
    }
    
    // Initialize Summernote
    const textEditors = document.querySelectorAll('.summernote');
    
    textEditors.forEach(function(editor) {
        try {
            $(editor).summernote({
                height: 300,
                toolbar: [
                    ['style', ['style']],
                    ['font', ['bold', 'underline', 'italic', 'clear']],
                    ['color', ['color']],
                    ['para', ['ul', 'ol', 'paragraph']],
                    ['table', ['table']],
                    ['insert', ['link', 'picture']],
                    ['view', ['fullscreen', 'codeview', 'help']]
                ],
                callbacks: {
                    onImageUpload: function(files) {
                        // Image upload handling if needed
                        console.log('Image upload triggered');
                    }
                }
            });
        } catch (error) {
            console.error('Error initializing Summernote:', error);
        }
    });
    
    // Initialize tooltips
    const tooltips = document.querySelectorAll('[data-bs-toggle="tooltip"]');
    tooltips.forEach(function(tooltip) {
        new bootstrap.Tooltip(tooltip);
    });
    
    // Auto-generate slug from name/title fields
    const nameField = document.querySelector('#id_name, #id_title');
    const slugField = document.querySelector('#id_slug');
    
    if (nameField && slugField) {
        nameField.addEventListener('keyup', function() {
            slugField.value = slugify(this.value);
        });
        
        // Only set initial value if slug field is empty
        if (slugField.value === '') {
            slugField.value = slugify(nameField.value);
        }
    }
    
    // Helper function to slugify text
    function slugify(text) {
        return text.toString().toLowerCase()
            .replace(/\s+/g, '-')           // Replace spaces with -
            .replace(/[^\w\-]+/g, '')       // Remove all non-word chars
            .replace(/\-\-+/g, '-')         // Replace multiple - with single -
            .replace(/^-+/, '')             // Trim - from start of text
            .replace(/-+$/, '');            // Trim - from end of text
    }
    
    // Handle Form Validation
    const forms = document.querySelectorAll('.needs-validation');
    
    forms.forEach(function(form) {
        form.addEventListener('submit', function(event) {
            if (!form.checkValidity()) {
                event.preventDefault();
                event.stopPropagation();
            }
            
            form.classList.add('was-validated');
        }, false);
    });
    
    // Subcategory dropdown dependency
    const categoryField = document.querySelector('#id_category');
    const subcategoryField = document.querySelector('#id_subcategory');
    
    // Skip this for the product form page which has its own more specialized handler
    const isProductFormPage = document.querySelector('.product-form') !== null;
    
    if (categoryField && subcategoryField && !isProductFormPage) {
        categoryField.addEventListener('change', function() {
            const categoryId = this.value;
            if (categoryId) {
                fetch(`/dashboard/api/subcategories-by-category/${categoryId}/`)
                    .then(response => response.json())
                    .then(data => {
                        // Clear current options
                        subcategoryField.innerHTML = '<option value="">---------</option>';
                        
                        // Add new options
                        data.forEach(subcategory => {
                            const option = document.createElement('option');
                            option.value = subcategory.id;
                            option.textContent = subcategory.name;
                            subcategoryField.appendChild(option);
                        });
                    })
                    .catch(error => console.error('Error loading subcategories:', error));
            } else {
                // Clear subcategory if no category selected
                subcategoryField.innerHTML = '<option value="">---------</option>';
            }
        });
    }
    
    // Confirmation dialogs for delete actions
    const deleteButtons = document.querySelectorAll('.delete-confirm');
    
    deleteButtons.forEach(function(button) {
        button.addEventListener('click', function(e) {
            if (!confirm('Are you sure you want to delete this item? This action cannot be undone.')) {
                e.preventDefault();
            }
        });
    });
    
    // Image Preview for uploads
    const imageInputs = document.querySelectorAll('input[type="file"][accept*="image"]');
    
    imageInputs.forEach(function(input) {
        const previewId = input.getAttribute('data-preview');
        if (previewId) {
            const preview = document.getElementById(previewId);
            
            input.addEventListener('change', function() {
                if (input.files && input.files[0]) {
                    const reader = new FileReader();
                    
                    reader.onload = function(e) {
                        preview.src = e.target.result;
                        preview.style.display = 'block';
                    };
                    
                    reader.readAsDataURL(input.files[0]);
                }
            });
        }
    });
    
    // Initialize Charts if any exists
    if (typeof Chart !== 'undefined') {
        // Sales Chart
        const salesChartEl = document.getElementById('salesChart');
        if (salesChartEl) {
            const salesChart = new Chart(salesChartEl, {
                type: 'line',
                data: {
                    labels: salesChartEl.getAttribute('data-labels').split(','),
                    datasets: [{
                        label: 'Sales',
                        data: salesChartEl.getAttribute('data-values').split(','),
                        backgroundColor: 'rgba(46, 125, 50, 0.1)',
                        borderColor: '#2e7d32',
                        tension: 0.3,
                        fill: true
                    }]
                },
                options: {
                    responsive: true,
                    plugins: {
                        legend: {
                            display: false
                        }
                    },
                    scales: {
                        y: {
                            beginAtZero: true
                        }
                    }
                }
            });
        }
        
        // Categories Chart
        const categoriesChartEl = document.getElementById('categoriesChart');
        if (categoriesChartEl) {
            const categoriesChart = new Chart(categoriesChartEl, {
                type: 'doughnut',
                data: {
                    labels: categoriesChartEl.getAttribute('data-labels').split(','),
                    datasets: [{
                        data: categoriesChartEl.getAttribute('data-values').split(','),
                        backgroundColor: [
                            '#2e7d32', // primary
                            '#ffb300', // secondary
                            '#17a2b8', // info
                            '#6c757d', // gray
                            '#fd7e14', // orange
                            '#6f42c1'  // purple
                        ]
                    }]
                },
                options: {
                    responsive: true,
                    plugins: {
                        legend: {
                            position: 'bottom'
                        }
                    }
                }
            });
        }
    }
}); 