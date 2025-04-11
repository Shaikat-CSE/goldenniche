from store.models import Category

def categories_processor(request):
    """
    Context processor to make categories available in all templates
    """
    categories = Category.objects.filter(is_active=True)
    return {'categories': categories} 