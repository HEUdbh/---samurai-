from django.db import models
import os


def upload_to(instance, filename):
    """生成简洁的存储路径：直接存放到 uploads/[类型]/ 目录"""
    # 通过MIME类型识别文件类别
    content_type = getattr(instance.file.file, 'content_type', '')
    file_type = 'video' if 'video' in content_type else 'text'

    # 构建目标路径（无需包含多层目录）
    target_dir = os.path.join('uploads', file_type)
    os.makedirs(target_dir, exist_ok=True)  # 自动创建目录（存在则跳过）

    return os.path.join(file_type, filename)  # 返回相对路径


class FileGroup(models.Model):
    """文件组：关联MP4和TXT文件"""
    video_file = models.FileField(
        upload_to='uploads/',
        null=True,  # 允许数据库中为空
        blank=True  # 允许表单中为空
    )
    text_file = models.FileField(
        upload_to='uploads/',
        null=True,
        blank=True
    )
    uploaded_at = models.DateTimeField(auto_now_add=True)
    processed = models.BooleanField(default=False)
    processed_video_path = models.CharField(
        max_length=255,
        null=True,
        blank=True,
        default=None
    )

    def __str__(self):
        return f"FileGroup {self.id}"

    @property
    def is_processed(self):
        return self.processed

    class Meta:
        db_table = 'myapp_filegroup'  # 确保使用正确的表名


class UploadedFile(models.Model):
    file = models.FileField(upload_to=upload_to)
    filename = models.CharField(max_length=255)
    file_type = models.CharField(max_length=10, editable=False)
    uploaded_at = models.DateTimeField(auto_now_add=True)
    file_group = models.ForeignKey(
        FileGroup,
        on_delete=models.CASCADE,
        related_name='files',
        null=True
    )

    def save(self, *args, **kwargs):
        # 自动识别文件类型
        self.file_type = self._get_file_type()
        super().save(*args, **kwargs)

    def _get_file_type(self):
        """通过MIME类型精确识别文件类型"""
        content_type = getattr(self.file.file, 'content_type', '')
        if 'video' in content_type:
            return 'video'
        elif 'text/plain' in content_type:
            return 'text'
        else:
            return 'unknown'

    @property
    def file_path(self):
        """获取文件的完整路径"""
        return self.file.path

    def __str__(self):
        return f"{self.filename} ({self.file_type})"

    class Meta:
        indexes = [
            models.Index(fields=['file_type']),
            models.Index(fields=['uploaded_at']),
        ]