# Generated by Django 4.1.5 on 2023-02-12 07:58

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('content', '0008_bookmark_created_at_hate_created_at_like_created_at_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='feed',
            name='comment_list',
            field=models.TextField(null='-'),
            preserve_default='-',
        ),
        migrations.AddField(
            model_name='userdata',
            name='latitude',
            field=models.FloatField(default=0),
        ),
        migrations.AddField(
            model_name='userdata',
            name='longitude',
            field=models.FloatField(default=0),
        ),
    ]