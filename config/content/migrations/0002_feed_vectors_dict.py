# Generated by Django 4.1.5 on 2023-01-17 14:52

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('content', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='feed',
            name='vectors_dict',
            field=models.TextField(null='{}'),
            preserve_default='{}',
        ),
    ]
