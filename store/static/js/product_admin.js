(function($) {
    $(document).ready(function() {
        console.log("Simple Product Admin JS loaded");
        
        // Get references to form fields
        var categorySelect = $('#id_category');
        var subcategorySelect = $('#id_subcategory');
        
        // Function to update subcategories
        function updateSubcategories() {
            var categoryId = categorySelect.val();
            
            // Clear subcategory if no category is selected
            if (!categoryId) {
                subcategorySelect.html('<option value="">---------</option>');
                return;
            }
            
            // Show loading indicator
            subcategorySelect.html('<option value="">Loading subcategories...</option>');
            
            // Get subcategories via AJAX
            $.ajax({
                url: '/get-subcategories/',
                data: { category_id: categoryId },
                dataType: 'json',
                success: function(data) {
                    // Remember current value
                    var currentValue = subcategorySelect.val();
                    
                    // Reset dropdown
                    subcategorySelect.empty();
                    subcategorySelect.append('<option value="">---------</option>');
                    
                    // Add subcategories
                    $.each(data, function(index, item) {
                        subcategorySelect.append(
                            $('<option></option>').attr('value', item.id).text(item.name)
                        );
                    });
                    
                    // Try to restore previous value if it exists in new options
                    if (currentValue) {
                        var exists = false;
                        subcategorySelect.find('option').each(function() {
                            if ($(this).val() == currentValue) {
                                exists = true;
                                return false; // break loop
                            }
                        });
                        
                        if (exists) {
                            subcategorySelect.val(currentValue);
                        }
                    }
                },
                error: function() {
                    subcategorySelect.html('<option value="">Error loading subcategories</option>');
                }
            });
        }
        
        // Update subcategories when category changes
        categorySelect.on('change', updateSubcategories);
        
        // Initial load
        if (categorySelect.val()) {
            updateSubcategories();
        }
    });
})(django.jQuery || jQuery); 