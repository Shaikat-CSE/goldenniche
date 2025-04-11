from django.db import migrations, models

class Migration(migrations.Migration):

    dependencies = [
        ('store', '0019_alter_review_unique_together_alter_review_rating_and_more'),
    ]

    operations = [
        migrations.RenameField(
            model_name='order',
            old_name='shipping_address',
            new_name='address',
        ),
        migrations.RenameField(
            model_name='order',
            old_name='total_amount',
            new_name='grand_total',
        ),
        migrations.AddField(
            model_name='order',
            name='city',
            field=models.CharField(default='', max_length=50),
        ),
        migrations.AddField(
            model_name='order',
            name='country',
            field=models.CharField(default='Bangladesh', max_length=50),
        ),
        migrations.AddField(
            model_name='order',
            name='email',
            field=models.EmailField(default='', max_length=254),
        ),
        migrations.AddField(
            model_name='order',
            name='first_name',
            field=models.CharField(default='', max_length=50),
        ),
        migrations.AddField(
            model_name='order',
            name='last_name',
            field=models.CharField(default='', max_length=50),
        ),
        migrations.AddField(
            model_name='order',
            name='phone',
            field=models.CharField(default='', max_length=15),
        ),
        migrations.AddField(
            model_name='order',
            name='zip_code',
            field=models.CharField(default='', max_length=10),
        ),
    ] 