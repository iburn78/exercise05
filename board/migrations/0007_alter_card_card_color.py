# Generated by Django 4.0.2 on 2022-03-01 06:58

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('board', '0006_auto_20220227_0132'),
    ]

    operations = [
        migrations.AlterField(
            model_name='card',
            name='card_color',
            field=models.CharField(default='bg-gray-200', max_length=30),
        ),
    ]
