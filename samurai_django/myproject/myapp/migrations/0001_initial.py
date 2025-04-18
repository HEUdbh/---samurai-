# Generated by Django 5.1.3 on 2025-04-14 10:23

import django.db.models.deletion
import myapp.models
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='FileGroup',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('video_file', models.FileField(blank=True, null=True, upload_to='uploads/')),
                ('text_file', models.FileField(blank=True, null=True, upload_to='uploads/')),
                ('uploaded_at', models.DateTimeField(auto_now_add=True)),
                ('processed', models.BooleanField(default=False)),
                ('processed_video_path', models.CharField(blank=True, default=None, max_length=255, null=True)),
            ],
            options={
                'db_table': 'myapp_filegroup',
            },
        ),
        migrations.CreateModel(
            name='UploadedFile',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('file', models.FileField(upload_to=myapp.models.upload_to)),
                ('filename', models.CharField(max_length=255)),
                ('file_type', models.CharField(editable=False, max_length=10)),
                ('uploaded_at', models.DateTimeField(auto_now_add=True)),
                ('file_group', models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, related_name='files', to='myapp.filegroup')),
            ],
            options={
                'indexes': [models.Index(fields=['file_type'], name='myapp_uploa_file_ty_021bbf_idx'), models.Index(fields=['uploaded_at'], name='myapp_uploa_uploade_6e644d_idx')],
            },
        ),
    ]
