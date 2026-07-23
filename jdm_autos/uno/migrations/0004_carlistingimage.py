from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('uno', '0003_alter_inquiry_options_inquiry_is_read_and_more'),
    ]

    operations = [
        migrations.CreateModel(
            name='CarListingImage',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('image', models.ImageField(upload_to='cars/gallery/')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('listing', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='gallery_images', to='uno.carlisting')),
            ],
            options={
                'ordering': ['created_at'],
            },
        ),
    ]
