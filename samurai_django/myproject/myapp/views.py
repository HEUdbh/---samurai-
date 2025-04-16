from django.shortcuts import render
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from django.utils import timezone
from .models import UploadedFile, FileGroup
from rest_framework.views import APIView
from django.core.files.storage import FileSystemStorage
from pathlib import Path
import os
import sys # 导入 sys 获取 python 执行路径
import subprocess # 导入 subprocess 执行外部命令
import logging
from django.conf import settings # 导入 settings 获取 BASE_DIR
from django.http import FileResponse
import shutil
from rest_framework.parsers import MultiPartParser, FormParser

# 配置日志
logger = logging.getLogger(__name__)

# 假设 settings.py 中的 BASE_DIR 指向 samurai_django/myproject
# 计算整个项目的根目录 (E:/model/samurai)
PROJECT_ROOT = settings.BASE_DIR.parent.parent

ALLOWED_TYPES = {
    'video': ['video/mp4'],
    'text': ['text/plain']
}

class ModelInferenceAPI(APIView):
    def post(self, request, group_id=None):
        logger.info(f"开始处理视频，group_id: {group_id}")
        try:
            if not group_id:
                logger.error("缺少文件组ID")
                return Response({
                    'status': 'error',
                    'message': '缺少文件组ID'
                }, status=400)

            # 获取文件组信息
            try:
                file_group = FileGroup.objects.get(id=group_id)
            except FileGroup.DoesNotExist:
                logger.error(f"找不到文件组: {group_id}")
                return Response({
                    'status': 'error',
                    'message': f'找不到文件组: {group_id}'
                }, status=404)

            # 检查文件是否存在
            if not file_group.video_file or not file_group.text_file:
                logger.error(f"文件组 {group_id} 缺少必要的文件")
                return Response({
                    'status': 'error',
                    'message': '文件组中缺少必要的文件'
                }, status=400)

            # 获取文件路径
            video_path = file_group.video_file.path
            txt_path = file_group.text_file.path

            # 记录文件路径
            logger.info(f"视频文件路径: {video_path}")
            logger.info(f"文本文件路径: {txt_path}")

            # 检查文件是否实际存在
            if not os.path.exists(video_path):
                logger.error(f"视频文件不存在: {video_path}")
                return Response({
                    'status': 'error',
                    'message': '视频文件不存在'
                }, status=404)
            if not os.path.exists(txt_path):
                logger.error(f"文本文件不存在: {txt_path}")
                return Response({
                    'status': 'error',
                    'message': '文本文件不存在'
                }, status=404)

            # 设置输出路径
            original_name = os.path.splitext(os.path.basename(video_path))[0]
            processed_dir = os.path.join(settings.MEDIA_ROOT, 'processed_videos')
            output_video_name = f'{original_name}_processed.mp4'
            output_video_path = os.path.join(processed_dir, output_video_name)

            # 确保输出目录存在
            os.makedirs(processed_dir, exist_ok=True)

            logger.info(f"输出视频路径: {output_video_path}")

            # 调用处理脚本
            script_path = os.path.join(PROJECT_ROOT, 'samurai_master', 'scripts', 'demo.py')
            cmd = [
                sys.executable,
                script_path,
                '--video_path', video_path,
                '--txt_path', txt_path
            ]
            
            logger.info(f"执行命令: {' '.join(cmd)}")
            
            try:
                result = subprocess.run(cmd, capture_output=True, text=True)
                logger.info(f"脚本输出: {result.stdout}")
                if result.stderr:
                    logger.error(f"脚本错误: {result.stderr}")
            except Exception as e:
                logger.error(f"执行脚本时出错: {str(e)}", exc_info=True)
                return Response({
                    'status': 'error',
                    'message': '视频处理脚本执行失败',
                    'detail': str(e)
                }, status=500)

            # 检查处理结果
            if result.returncode == 0:
                # 直接检查输出路径，因为 demo.py 已经将文件保存在正确位置
                if os.path.exists(output_video_path):
                    # 构建URL
                    relative_path = os.path.relpath(output_video_path, settings.MEDIA_ROOT)
                    video_url = request.build_absolute_uri(settings.MEDIA_URL + relative_path.replace('\\', '/'))
                    
                    # 更新文件组状态
                    file_group.processed = True
                    file_group.processed_video_path = output_video_path
                    file_group.save()

                    logger.info(f"视频处理成功，URL: {video_url}")
                    return Response({
                        'status': 'success',
                        'message': '视频处理完成',
                        'video_url': video_url,
                        'video_name': output_video_name
                    })
                else:
                    logger.error(f"处理后的视频文件未找到: {output_video_path}")
                    return Response({
                        'status': 'error',
                        'message': '处理后的视频文件未找到',
                        'detail': f'File not found: {output_video_path}'
                    }, status=404)
            else:
                logger.error(f"视频处理失败: {result.stderr}")
                return Response({
                    'status': 'error',
                    'message': '视频处理失败',
                    'detail': result.stderr
                }, status=500)

        except Exception as e:
            logger.exception("处理视频时发生未预期的错误")
            return Response({
                'status': 'error',
                'message': str(e),
                'detail': '处理视频时发生未预期的错误'
            }, status=500)

class FileUploadAPI(APIView):
    parser_classes = (MultiPartParser, FormParser)

    def post(self, request):
        try:
            logger.info("开始处理文件上传请求")
            
            # 检查是否有文件
            if 'video' not in request.FILES:
                logger.error("请求中没有视频文件")
                return Response({
                    'status': 'error',
                    'error': '请上传视频文件'
                }, status=status.HTTP_400_BAD_REQUEST)

            if 'text' not in request.FILES:
                logger.error("请求中没有文本文件")
                return Response({
                    'status': 'error',
                    'error': '请上传文本文件'
                }, status=status.HTTP_400_BAD_REQUEST)

            video_file = request.FILES['video']
            text_file = request.FILES['text']

            # 验证文件类型
            if not video_file.name.lower().endswith('.mp4'):
                logger.error(f"无效的视频文件类型: {video_file.name}")
                return Response({
                    'status': 'error',
                    'error': '请上传MP4格式的视频文件'
                }, status=status.HTTP_400_BAD_REQUEST)

            if not text_file.name.lower().endswith('.txt'):
                logger.error(f"无效的文本文件类型: {text_file.name}")
                return Response({
                    'status': 'error',
                    'error': '请上传TXT格式的文本文件'
                }, status=status.HTTP_400_BAD_REQUEST)

            # 创建文件组
            file_group = FileGroup(
                video_file=video_file,
                text_file=text_file
            )

            # 确保上传目录存在
            upload_dir = os.path.join(settings.MEDIA_ROOT, 'uploads')
            os.makedirs(upload_dir, exist_ok=True)

            try:
                file_group.save()
                logger.info(f"文件组保存成功，ID: {file_group.id}")
                
                # 验证文件是否实际保存
                if not os.path.exists(file_group.video_file.path):
                    raise Exception("视频文件未能成功保存到磁盘")
                if not os.path.exists(file_group.text_file.path):
                    raise Exception("文本文件未能成功保存到磁盘")

            except Exception as e:
                logger.error(f"保存文件组时出错: {str(e)}")
                # 如果保存失败，确保清理任何可能已经创建的文件
                if file_group.id:
                    file_group.delete()
                return Response({
                    'status': 'error',
                    'error': f'保存文件失败: {str(e)}'
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

            # 返回成功响应
            return Response({
                'status': 'success',
                'message': '文件上传成功',
                'group_id': file_group.id
            }, status=status.HTTP_201_CREATED)

        except Exception as e:
            logger.error(f"文件上传过程中发生未预期的错误: {str(e)}", exc_info=True)
            return Response({
                'status': 'error',
                'error': f'上传失败: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['GET'])
def get_process_status(request, group_id):
    """获取文件处理状态和详细信息"""
    try:
        file_group = FileGroup.objects.get(id=group_id)
        
        # 获取视频和文本文件信息
        video_file = file_group.video_file
        text_file = file_group.text_file

        response_data = {
            'status': 'completed' if file_group.processed else 'processing',
            'group_id': group_id,
            'upload_time': file_group.created_at,
            'process_completed_time': file_group.processed_at,
            'is_processed': file_group.processed,
            'files': {
                'video': {
                    'filename': video_file.filename if video_file else None,
                    'path': video_file.path if video_file else None,
                    'upload_time': video_file.uploaded_at if video_file else None,
                } if video_file else None,
                'text': {
                    'filename': text_file.filename if text_file else None,
                    'path': text_file.path if text_file else None,
                    'upload_time': text_file.uploaded_at if text_file else None,
                } if text_file else None
            }
        }

        # 如果处理完成，添加处理结果信息
        if file_group.processed:
            response_data['message'] = '处理已完成'
            # TODO: 添加处理结果的具体信息
            response_data['result'] = {
                'processed_video_path': file_group.processed_video_path,
                # 添加其他处理结果信息
            }
        else:
            response_data['message'] = '处理中...'

        return Response(response_data)

    except FileGroup.DoesNotExist:
        return Response({
            'error': '找不到指定的文件组',
            'group_id': group_id
        }, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        return Response({
            'error': str(e),
            'group_id': group_id
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

# 添加新的视图用于获取处理后的视频
class GetProcessedVideoAPI(APIView):
    def get(self, request, group_id):
        try:
            file_group = FileGroup.objects.get(id=group_id)
            if not file_group.processed or not file_group.processed_video_path:
                return Response({
                    'status': 'error',
                    'error': '视频尚未处理完成'
                }, status=status.HTTP_404_NOT_FOUND)

            # 检查文件是否存在
            if not os.path.exists(file_group.processed_video_path):
                return Response({
                    'status': 'error',
                    'error': '处理后的视频文件不存在'
                }, status=status.HTTP_404_NOT_FOUND)

            # 返回视频文件
            return FileResponse(
                open(file_group.processed_video_path, 'rb'),
                content_type='video/mp4',
                as_attachment=False
            )
        except FileGroup.DoesNotExist:
            return Response({
                'status': 'error',
                'error': '文件组不存在'
            }, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            logger.error(f"获取处理后视频时发生错误: {str(e)}", exc_info=True)
            return Response({
                'status': 'error',
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['GET'])
def health_check(request):
    """健康检查端点"""
    try:
        return Response({
            'status': 'success',
            'message': '服务正常运行'
        })
    except Exception as e:
        return Response({
            'status': 'error',
            'message': str(e)
        }, status=500)