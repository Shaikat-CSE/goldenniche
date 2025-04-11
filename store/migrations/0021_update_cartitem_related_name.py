from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('store', '0020_update_order_fields'),
    ]

    operations = [
        migrations.AlterField(
            model_name='cartitem',
            name='cart',
            field=models.ForeignKey(on_delete=models.CASCADE, related_name='items', to='store.cart'),
        ),
    ] 