# Generated by Django 3.2.5 on 2021-09-02 07:51

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('sites', '0005_site_memo'),
    ]

    operations = [
        migrations.AlterField(
            model_name='site',
            name='ckanapi_url',
            field=models.URLField(verbose_name='API URL'),
        ),
        migrations.AlterField(
            model_name='site',
            name='contact',
            field=models.CharField(blank=True, max_length=255, null=True, verbose_name='連絡先'),
        ),
        migrations.AlterField(
            model_name='site',
            name='dataset_url',
            field=models.URLField(unique=True, verbose_name='データセットURL'),
        ),
        migrations.AlterField(
            model_name='site',
            name='enable',
            field=models.BooleanField(default=True, verbose_name='更新実行可'),
        ),
        migrations.AlterField(
            model_name='site',
            name='is_fq_available',
            field=models.BooleanField(default=True, verbose_name='差分更新可'),
        ),
        migrations.AlterField(
            model_name='site',
            name='proxy_url',
            field=models.URLField(blank=True, null=True, verbose_name='Proxy URL'),
        ),
        migrations.AlterField(
            model_name='site',
            name='publisher',
            field=models.CharField(blank=True, max_length=255, null=True, verbose_name='発行者'),
        ),
        migrations.AlterField(
            model_name='site',
            name='publisher_url',
            field=models.URLField(blank=True, null=True, verbose_name='発行者URL'),
        ),
    ]
