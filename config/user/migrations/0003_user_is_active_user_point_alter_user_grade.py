# Generated by Django 4.1.5 on 2023-01-19 17:10

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('user', '0002_alter_user_email_alter_user_nickname'),
    ]

    operations = [
        migrations.AddField(
            model_name='user',
            name='is_active',
            field=models.TextField(default='active'),
        ),
        migrations.AddField(
            model_name='user',
            name='point',
            field=models.IntegerField(default=0),
        ),
        migrations.AlterField(
            model_name='user',
            name='grade',
            field=models.TextField(default='-'),
        ),
    ]
