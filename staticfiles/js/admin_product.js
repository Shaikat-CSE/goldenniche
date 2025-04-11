(function($) {
    $(document).ready(function() {
        // Only run this script on product admin page
        if (!$('#id_category').length || !$('#id_subcategory').length) {
            return;
        }
        
        console.log("Product admin form detected - initializing dynamic subcategories");
        
        var categorySelect = $('#id_category');
        var subcategorySelect = $('#id_subcategory');
        
        function updateSubcategories() {
            console.log("Updating subcategories");
            var categoryId = categorySelect.val();
            
            if (categoryId) {
                console.log("Selected category ID:", categoryId);
                
                // Save current selected subcategory if any
                var currentSubcategoryId = subcategorySelect.val();
                
                // Show loading indicator
                subcategorySelect.html('<option value="">Loading subcategories...</option>');
                
                // Fetch subcategories via AJAX
                $.ajax({
                    url: '/get-subcategories/',
                    data: { category_id: categoryId },
                    dataType: 'json',
                    success: function(data) {
                        console.log("Received subcategories:", data);
                        
                        // Clear and populate subcategory dropdown
                        subcategorySelect.empty();
                        subcategorySelect.append($('<option value="">---------</option>'));
                        
                        $.each(data, function(index, subcategory) {
                            var option = $('<option></option>')
                                .attr('value', subcategory.id)
                                .text(subcategory.name);
                                
                            // Re-select previously selected subcategory if it exists
                            if (subcategory.id == currentSubcategoryId) {
                                option.attr('selected', 'selected');
                            }
                            
                            subcategorySelect.append(option);
                        });
                        
                        // Enable subcategory select
                        subcategorySelect.prop('disabled', false);
                    },
                    error: function(xhr, status, error) {
                        console.error("Error fetching subcategories:", error);
                        subcategorySelect.html('<option value="">Error loading subcategories</option>');
                    }
                });
            } else {
                // No category selected, clear subcategories
                console.log("No category selected, clearing subcategories");
                subcategorySelect.empty();
                subcategorySelect.append($('<option value="">---------</option>'));
                subcategorySelect.prop('disabled', true);
            }
        }
        
        // Bind change event to category select
        categorySelect.on('change', updateSubcategories);
        
        // Initial update on page load if category is already selected
        if (categorySelect.val()) {
            updateSubcategories();
        }
    });
})(django.jQuery);
