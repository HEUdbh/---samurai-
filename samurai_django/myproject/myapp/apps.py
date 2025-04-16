from django.apps import AppConfig


class MyappConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'myapp'


# myapp/apps.py
from django.apps import AppConfig
from .services.ml_service import SamuraiModel


class MyappConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'myapp'

    def ready(self):
        # 开发环境下自动启动服务
        if not self._is_management_command():
            # 移除或注释掉与 service_manager 或 SamuraiModel 相关的初始化和启动代码
            pass

    def _is_management_command(self):
        """判断是否在运行管理命令"""
        import sys
        return sys.argv and 'manage.py' in sys.argv[0] and 'runserver' not in sys.argv