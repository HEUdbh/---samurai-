from django.urls import path
from .views import FileUploadAPI, ModelInferenceAPI, GetProcessedVideoAPI, health_check

urlpatterns = [
    path('upload/', FileUploadAPI.as_view(), name='upload_files'),
    path('process/<int:group_id>/', ModelInferenceAPI.as_view(), name='process_files'),
    path('video/<int:group_id>/', GetProcessedVideoAPI.as_view(), name='get_video'),
    path('health/', health_check, name='health_check'),
]