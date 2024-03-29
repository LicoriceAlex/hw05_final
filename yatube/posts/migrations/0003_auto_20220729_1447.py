# Generated by Django 2.2.19 on 2022-07-29 09:47

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('posts', '0002_auto_20220729_1420'),
    ]

    operations = [
        migrations.AlterField(
            model_name='group',
            name='slug',
            field=models.CharField(max_length=50),
        ),
        migrations.AlterField(
            model_name='post',
            name='group',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='posts.Group'),
        ),
    ]
