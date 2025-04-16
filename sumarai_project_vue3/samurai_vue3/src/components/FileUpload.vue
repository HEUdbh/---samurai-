<template>
  <div class="file-uploader">
    <!-- 主要内容区域：文件上传和视频播放并列 -->
    <div class="main-content">
      <!-- 左侧上传区域 -->
      <div class="upload-container">
        <div class="upload-section">
          <div class="file-input-group">
            <h3>视频文件 (MP4)</h3>
            <input 
              type="file"
              accept="video/mp4"
              @change="handleVideoSelect"
              :disabled="uploading"
            />
            <div v-if="videoFile" class="selected-file">
              已选择: {{ videoFile.name }}
            </div>
          </div>

          <div class="file-input-group">
            <h3>文本文件 (TXT)</h3>
            <input 
              type="file"
              accept=".txt"
              @change="handleTextSelect"
              :disabled="uploading"
            />
            <div v-if="textFile" class="selected-file">
              已选择: {{ textFile.name }}
            </div>
          </div>
        </div>

        <!-- 上传按钮 -->
        <button 
          @click="handleUploadAndProcess" 
          :disabled="!canUpload || uploading"
          class="action-button"
        >
          {{ uploading ? '上传中...' : '上传文件' }}
        </button>

        <!-- 处理按钮 -->
        <button 
          v-if="groupId && !processing"
          @click="processFiles"
          :disabled="processing || isProcessed"
          class="action-button process-button"
        >
          {{ isProcessed ? '处理完成' : '开始处理' }}
        </button>

        <!-- 上传进度条 -->
        <div v-if="uploading" class="progress-container">
          <div class="progress-label">上传进度</div>
          <div class="progress-bar">
            <div class="progress-fill" :style="{ width: `${uploadProgress}%` }"></div>
          </div>
          <div class="progress-text">{{ uploadProgress }}%</div>
        </div>

        <!-- 处理进度状态 -->
        <div v-if="processing" class="progress-container">
          <div class="progress-label">处理中...</div>
          <div class="processing-spinner"></div>
        </div>

        <!-- 简化的状态消息 -->
        <div v-if="message" class="status-message" :class="messageType">
          {{ message }}
        </div>
      </div>

      <!-- 右侧视频区域 -->
      <div v-if="processedVideoUrl && isProcessed" class="video-section">
        <div class="video-player-container">
          <h4>处理后的视频</h4>
          
          <!-- 视频播放器 -->
          <div class="video-wrapper">
            <video 
              ref="videoPlayer"
              class="video-player"
              controls
              @error="handleVideoError"
              @loadeddata="handleVideoLoaded"
              crossorigin="anonymous"
            >
              <source :src="processedVideoUrl" type="video/mp4; codecs='avc1.42E01E, mp4a.40.2'">
              您的浏览器不支持 HTML5 视频播放
            </video>
            
            <!-- 加载提示 -->
            <div v-if="isVideoLoading" class="video-loading">
              <div class="loading-spinner"></div>
              <span>视频加载中...</span>
            </div>
          </div>

          <!-- 视频控制按钮 -->
          <div class="video-controls">
            <button 
              @click="handleDownload"
              class="control-button download-button"
            >
              <span class="button-icon">⭳</span>
              下载视频
            </button>
            
            <button 
              v-if="videoError"
              @click="reloadVideo"
              class="control-button reload-button"
            >
              <span class="button-icon">↻</span>
              重新加载
            </button>
          </div>

          <!-- 错误提示 -->
          <div v-if="videoError" class="video-error">
            <p>{{ videoError }}</p>
          </div>
        </div>
      </div>
    </div>

    <!-- 底部日志区域 -->
    <div v-if="showProcessLog" class="result-section">
      <h3>处理结果</h3>
      <div class="log-header">
        <span>{{ isProcessed ? '处理完成' : (hasError ? '处理出错' : '处理状态') }}</span>
      </div>
      
      <!-- 处理日志 -->
      <div v-if="logContent" class="log-content-wrapper">
        <pre class="log-content">{{ logContent }}</pre>
      </div>
    </div>

    <!-- 错误信息显示 -->
    <div v-if="logContent && logContent.includes('错误')" class="error-container">
      <div class="error-message">
        <h4>处理过程中遇到问题：</h4>
        <pre class="error-details">{{ logContent }}</pre>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue';
import axios from 'axios';

// 状态变量
const videoFile = ref<File | null>(null);
const textFile = ref<File | null>(null);
const uploading = ref(false);
const processing = ref(false);
const uploadProgress = ref(0);
const message = ref('');
const messageType = ref<'success' | 'error'>('success');
const groupId = ref<number | null>(null);
const isProcessed = ref(false);
const showProcessLog = ref(false); // 控制是否显示处理日志
const hasError = ref(false); // 是否存在错误
const logContent = ref(''); // 处理日志内容
const detailedError = ref(''); // 详细错误信息
const showDetailedError = ref(false); // 控制是否显示详细错误
const processedVideoUrl = ref<string | null>(null);
const videoPlayer = ref<HTMLVideoElement | null>(null);
const showResult = ref(false);
const isVideoLoading = ref(true);
const videoError = ref<string | null>(null);

// 计算属性
const canUpload = computed(() => {
  return videoFile.value && textFile.value && !uploading.value;
});

// 文件选择处理
const handleVideoSelect = (e: Event) => {
  const input = e.target as HTMLInputElement;
  if (input.files && input.files[0]) {
    const file = input.files[0];
    if (file.type === 'video/mp4') {
      videoFile.value = file;
      resetVideoState();  // 重置视频状态
      showProcessLog.value = false;  // 隐藏之前的处理结果
      isProcessed.value = false;  // 重置处理状态
    } else {
      showMessage('请选择MP4格式的视频文件', 'error');
    }
  }
};

const handleTextSelect = (e: Event) => {
  const input = e.target as HTMLInputElement;
  if (input.files && input.files[0]) {
    const file = input.files[0];
    if (file.type === 'text/plain') {
      textFile.value = file;
    } else {
      showMessage('请选择TXT格式的文本文件', 'error');
    }
  }
};

// 显示消息
const showMessage = (msg: string, type: 'success' | 'error') => {
  message.value = msg;
  messageType.value = type;
  
  // 3秒后自动清除消息
  setTimeout(() => {
    message.value = '';
  }, 3000);
};

// 更新日志内容
const updateLogContent = (content: any) => {
  if (typeof content === 'string') {
    logContent.value = content;
  } else if (content && typeof content === 'object') {
    try {
      // 从对象中提取简洁信息
      if (content.message) {
        logContent.value = content.message;
      } else if (content.status && content.result) {
        logContent.value = `状态: ${content.status}\n结果: ${JSON.stringify(content.result, null, 2)}`;
      } else {
        // 完整对象
        logContent.value = JSON.stringify(content, null, 2);
      }
    } catch (e) {
      logContent.value = '无法解析日志内容';
    }
  } else {
    logContent.value = '无日志内容';
  }
};

// 获取视频文件名
const getVideoFileName = () => {
  if (videoFile.value) {
    const originalName = videoFile.value.name;
    const baseName = originalName.replace(/\.mp4$/, '');
    return `${baseName}_processed.mp4`;
  }
  return 'processed_video.mp4';
};

// 处理视频加载完成
const handleVideoLoaded = () => {
  isVideoLoading.value = false;
  videoError.value = null;
};

// 处理视频错误
const handleVideoError = async (e: Event) => {
  const target = e.target as HTMLVideoElement;
  isVideoLoading.value = false;
  
  let errorMessage = '视频加载失败: ';
  if (target.error) {
    switch (target.error.code) {
      case MediaError.MEDIA_ERR_ABORTED:
        errorMessage += '加载被中断';
        break;
      case MediaError.MEDIA_ERR_NETWORK:
        errorMessage += '网络错误';
        break;
      case MediaError.MEDIA_ERR_DECODE:
      case MediaError.MEDIA_ERR_SRC_NOT_SUPPORTED:
        errorMessage += '视频格式不支持';
        // 尝试重新加载
        await retryLoadVideo();
        break;
      default:
        errorMessage += `未知错误 (${target.error.code})`;
    }
  }
  
  videoError.value = errorMessage;
  console.error('视频加载错误:', {
    url: processedVideoUrl.value,
    error: target.error,
    errorMessage
  });
};

// 重新加载视频
const reloadVideo = () => {
  if (videoPlayer.value) {
    isVideoLoading.value = true;
    videoError.value = null;
    videoPlayer.value.load();
  }
};

// 处理下载
const handleDownload = async () => {
  if (!processedVideoUrl.value) {
    showMessage('视频文件不可用', 'error');
    return;
  }

  try {
    // 添加时间戳防止缓存
    const timestamp = new Date().getTime();
    const downloadUrl = `${processedVideoUrl.value}?t=${timestamp}`;
    
    // 先检查文件是否可访问
    const checkResponse = await fetch(downloadUrl, {
      method: 'HEAD'
    });

    if (!checkResponse.ok) {
      throw new Error(`文件访问失败: ${checkResponse.status}`);
    }

    // 使用 fetch API 下载
    const response = await fetch(downloadUrl);
    const blob = await response.blob();
    
    // 检查内容类型
    const contentType = response.headers.get('content-type');
    if (!contentType || !contentType.includes('video/mp4')) {
      console.warn('警告: 响应的内容类型不是 video/mp4:', contentType);
    }

    // 创建下载链接
    const url = window.URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = getVideoFileName(); // 使用原始文件名
    
    // 添加到文档并触发点击
    document.body.appendChild(link);
    link.click();
    
    // 清理
    setTimeout(() => {
      document.body.removeChild(link);
      window.URL.revokeObjectURL(url);
    }, 100);

    showMessage('下载开始', 'success');
  } catch (error: any) {
    console.error('下载失败:', error);
    showMessage(`下载失败: ${error.message}`, 'error');
    logContent.value += `下载错误: ${error.message}\n`;
  }
};

// 添加视频可访问性检查函数
const checkVideoAccessibility = async (url: string) => {
  try {
    const response = await fetch(url, {
      method: 'HEAD',
      mode: 'cors'
    });
    
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }
    
    return true;
  } catch (e) {
    console.error('视频访问检查失败:', e);
    return false;
  }
};

// 添加视频格式检查函数
const checkVideoFormat = async (url: string): Promise<boolean> => {
  try {
    const response = await fetch(url, {
      method: 'HEAD'
    });

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }

    const contentType = response.headers.get('content-type');
    return contentType !== null && contentType.includes('video/mp4');
  } catch (e) {
    console.error('视频格式检查失败:', e);
    return false;
  }
};

// 添加视频重试加载函数
const retryLoadVideo = async () => {
  if (!processedVideoUrl.value) return;
  
  try {
    isVideoLoading.value = true;
    videoError.value = null;
    
    // 添加时间戳防止缓存
    const timestamp = new Date().getTime();
    const newUrl = `${processedVideoUrl.value}?t=${timestamp}`;
    
    // 检查视频格式
    const isValidFormat = await checkVideoFormat(newUrl);
    if (!isValidFormat) {
      throw new Error('视频格式不正确');
    }
    
    // 更新视频 URL 并重新加载
    processedVideoUrl.value = newUrl;
    if (videoPlayer.value) {
      videoPlayer.value.load();
    }
  } catch (error: any) {
    console.error('重试加载失败:', error);
    videoError.value = `无法加载视频: ${error.message}`;
    isVideoLoading.value = false;
  }
};

// 修改处理文件的函数
const handleUploadAndProcess = async () => {
  if (!videoFile.value || !textFile.value) return;

  uploading.value = true;
  uploadProgress.value = 0;
  showResult.value = true;
  showProcessLog.value = true;  // 添加这行，确保处理日志区域显示
  logContent.value = '开始上传文件...\n';

  try {
    // 第一步：上传文件
    const formData = new FormData();
    formData.append('video', videoFile.value);
    formData.append('text', textFile.value);

    const uploadResponse = await axios.post(
      'http://localhost:8000/api/upload/',
      formData,
      {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
        onUploadProgress: (progressEvent) => {
          if (progressEvent.total) {
            uploadProgress.value = Math.round(
              (progressEvent.loaded * 100) / progressEvent.total
            );
          }
        }
      }
    );

    if (uploadResponse.data.status !== 'success') {
      throw new Error(uploadResponse.data.error || '文件上传失败');
    }

    const groupId = uploadResponse.data.group_id;
    logContent.value += '文件上传成功，开始处理...\n';
    uploading.value = false;
    processing.value = true;

    // 第二步：处理文件
    const processResponse = await axios.post(
      `http://localhost:8000/api/process/${groupId}/`
    );

    if (processResponse.data.status === 'success') {
      processing.value = false;
      isProcessed.value = true;
      showMessage('处理完成！', 'success');
      logContent.value += '处理完成！\n';

      // 构建完整的视频 URL
      const videoUrl = processResponse.data.video_url;
      const timestamp = new Date().getTime();
      const fullVideoUrl = `${videoUrl}?t=${timestamp}`;
      
      // 检查视频是否可访问
      const isValidFormat = await checkVideoFormat(fullVideoUrl);
      if (isValidFormat) {
        processedVideoUrl.value = fullVideoUrl;
        logContent.value += `视频可访问: ${fullVideoUrl}\n`;
        showResult.value = true;
        showProcessLog.value = true;
        isVideoLoading.value = true;
        videoError.value = null;
      } else {
        throw new Error('处理后的视频格式不正确或无法访问');
      }
    } else {
      throw new Error(processResponse.data.message || '视频处理失败');
    }

  } catch (error: any) {
    const errorMessage = error.response?.data?.error || 
                        error.response?.data?.message || 
                        error.message || 
                        '操作失败';
    showMessage(errorMessage, 'error');
    logContent.value += `错误: ${errorMessage}\n`;
    hasError.value = true;  // 添加这行，标记错误状态
    console.error('操作错误:', error);
  } finally {
    uploading.value = false;
    processing.value = false;
  }
};

// 添加视频状态重置函数
const resetVideoState = () => {
  isVideoLoading.value = true;
  videoError.value = null;
  processedVideoUrl.value = null;
};

// 添加一个用于检查后端状态的函数
const checkBackendStatus = async () => {
  try {
    await axios.get('http://localhost:8000/api/health/');
    return true;
  } catch (error) {
    console.error('后端服务检查失败:', error);
    return false;
  }
};

// 在组件挂载时检查后端状态
onMounted(async () => {
  const isBackendAvailable = await checkBackendStatus();
  if (!isBackendAvailable) {
    showMessage('无法连接到后端服务，请确保服务已启动', 'error');
  }
});

// 处理处理错误
const handleProcessError = (error: any) => {
  // 更新简洁错误日志
  logContent.value += '\n处理过程中出错。需要安装缺失的依赖，请查看详细错误。';
  
  // 存储详细错误信息
  if (error.response?.data?.error) {
    detailedError.value = error.response.data.error;
  } else if (error.response?.data?.result?.script_stderr) {
    detailedError.value = error.response.data.result.script_stderr;
  } else if (error.message) {
    detailedError.value = error.message;
  }
};
</script>

<style scoped>
.file-uploader {
  max-width: 1200px;  /* 增加整体宽度 */
  margin: 3rem auto;
  padding: 2.5rem;
  border: none;
  border-radius: 16px;
  background: #ffffff;
  box-shadow: 0 8px 30px rgba(0, 0, 0, 0.08);
  transition: all 0.3s ease;
}

.main-content {
  display: grid;
  grid-template-columns: 1fr 1fr;  /* 两列等宽布局 */
  gap: 2rem;
  margin-bottom: 2rem;
  min-height: 500px;  /* 确保有足够的高度 */
}

.upload-container {
  display: flex;
  flex-direction: column;
  gap: 1.5rem;
}

.upload-section {
  display: flex;
  flex-direction: column;
  gap: 1.5rem;
}

.file-input-group {
  background: #f8fafc;
  padding: 1.5rem;
  border-radius: 12px;
  border: 1px solid rgba(0, 0, 0, 0.05);
  transition: all 0.3s ease;
}

.file-input-group:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.05);
}

.file-input-group h3 {
  margin: 0 0 1rem 0;
  font-size: 1.1rem;
  color: #1a1a1a;
  font-weight: 600;
}

.selected-file {
  margin-top: 0.8rem;
  font-size: 0.95rem;
  color: #4a5568;
  padding: 0.5rem;
  background: rgba(66, 185, 131, 0.1);
  border-radius: 6px;
}

.action-button {
  width: 100%;
  padding: 1rem;
  background: linear-gradient(135deg, #42b983 0%, #3aa876 100%);
  color: white;
  border: none;
  border-radius: 8px;
  cursor: pointer;
  font-size: 1.1rem;
  margin-bottom: 1.2rem;
  transition: all 0.3s ease;
  font-weight: 500;
  letter-spacing: 0.5px;
  box-shadow: 0 4px 12px rgba(66, 185, 131, 0.2);
}

.action-button:hover:not(:disabled) {
  transform: translateY(-2px);
  box-shadow: 0 6px 16px rgba(66, 185, 131, 0.3);
}

.action-button:disabled {
  background: linear-gradient(135deg, #a8d5c2 0%, #9ecbb8 100%);
  cursor: not-allowed;
  box-shadow: none;
}

.process-button {
  background: linear-gradient(135deg, #4a90e2 0%, #357abd 100%);
  box-shadow: 0 4px 12px rgba(74, 144, 226, 0.2);
}

.process-button:hover:not(:disabled) {
  box-shadow: 0 6px 16px rgba(74, 144, 226, 0.3);
}

.process-button:disabled {
  background: linear-gradient(135deg, #a8c4e2 0%, #9ab8d9 100%);
}

.progress-container {
  background: #f8fafc;
  padding: 1.2rem;
  border-radius: 10px;
  box-shadow: inset 0 2px 4px rgba(0, 0, 0, 0.05);
}

.progress-label {
  margin-bottom: 0.8rem;
  color: #4a5568;
  font-weight: 500;
}

.progress-bar {
  height: 10px;
  background: #e2e8f0;
  border-radius: 6px;
  overflow: hidden;
  box-shadow: inset 0 2px 4px rgba(0, 0, 0, 0.05);
}

.progress-fill {
  height: 100%;
  background: linear-gradient(90deg, #42b983 0%, #3aa876 100%);
  transition: width 0.4s ease;
  box-shadow: 0 2px 4px rgba(66, 185, 131, 0.2);
}

.progress-text {
  text-align: right;
  font-size: 0.95rem;
  color: #4a5568;
  margin-top: 0.5rem;
  font-weight: 500;
}

.processing-spinner {
  width: 30px;
  height: 30px;
  border: 3px solid rgba(66, 185, 131, 0.1);
  border-top: 3px solid #42b983;
  border-radius: 50%;
  animation: spin 1s linear infinite;
  margin: 1rem auto;
}

.status-message {
  padding: 1.2rem;
  margin: 1.2rem 0;
  border-radius: 10px;
  text-align: center;
  font-weight: 500;
  animation: fadeIn 0.3s ease;
}

.success {
  background: linear-gradient(135deg, #d4edda 0%, #c3e6cb 100%);
  color: #155724;
  box-shadow: 0 2px 8px rgba(21, 87, 36, 0.1);
}

.error {
  background: linear-gradient(135deg, #f8d7da 0%, #f5c6cb 100%);
  color: #721c24;
  box-shadow: 0 2px 8px rgba(114, 28, 36, 0.1);
}

.result-section {
  margin-top: 2rem;
  padding: 1.5rem;
  background: #f8fafc;
  border-radius: 12px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.05);
  display: block;  /* 改为块级布局 */
}

.log-header {
  margin-bottom: 1rem;
  font-weight: 500;
}

.log-content-wrapper {
  margin-bottom: 1.2rem;
  height: 100%;  /* 填充整个高度 */
}

.log-content {
  max-height: 300px;  /* 减小日志区域高度 */
  overflow-y: auto;
  background: #ffffff;
  padding: 1.2rem;
  border-radius: 8px;
  font-family: 'Monaco', 'Menlo', monospace;
  line-height: 1.5;
  border: 1px solid #e2e8f0;
}

.video-section {
  background: #ffffff;
  border-radius: 12px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.05);
  height: fit-content;
  position: sticky;
  top: 2rem;
}

.video-player-container {
  background: #ffffff;
  border-radius: 12px;
  overflow: hidden;
}

.video-wrapper {
  aspect-ratio: 16/9;
  background: #000000;
  position: relative;
}

.video-player {
  width: 100%;
  max-width: 100%;
  display: block;
  border-radius: 8px;
}

.video-loading {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  background: rgba(0, 0, 0, 0.8);
  color: white;
  backdrop-filter: blur(4px);
}

.loading-spinner {
  width: 48px;
  height: 48px;
  border: 4px solid rgba(255, 255, 255, 0.2);
  border-top: 4px solid #ffffff;
  border-radius: 50%;
  animation: spin 1s linear infinite;
  margin-bottom: 1.2rem;
}

.video-controls {
  padding: 1rem;
  border-top: 1px solid #e2e8f0;
  background: #f8fafc;
}

.control-button {
  display: inline-flex;
  align-items: center;
  gap: 0.8rem;
  padding: 0.8rem 1.5rem;
  border: none;
  border-radius: 8px;
  cursor: pointer;
  font-size: 1rem;
  transition: all 0.3s ease;
  font-weight: 500;
  letter-spacing: 0.5px;
}

.download-button {
  background: linear-gradient(135deg, #42b983 0%, #3aa876 100%);
  color: white;
  text-decoration: none;
  box-shadow: 0 4px 12px rgba(66, 185, 131, 0.2);
}

.download-button:hover {
  transform: translateY(-2px);
  box-shadow: 0 6px 16px rgba(66, 185, 131, 0.3);
}

.reload-button {
  background: linear-gradient(135deg, #4a90e2 0%, #357abd 100%);
  color: white;
  box-shadow: 0 4px 12px rgba(74, 144, 226, 0.2);
}

.reload-button:hover {
  transform: translateY(-2px);
  box-shadow: 0 6px 16px rgba(74, 144, 226, 0.3);
}

.button-icon {
  font-size: 1.3rem;
}

.video-error {
  margin-top: 1.2rem;
  padding: 1rem;
  background: linear-gradient(135deg, #f8d7da 0%, #f5c6cb 100%);
  border: 1px solid #f5c6cb;
  border-radius: 8px;
  color: #721c24;
  text-align: center;
  font-weight: 500;
  box-shadow: 0 2px 8px rgba(114, 28, 36, 0.1);
}

.error-container {
  margin: 1.2rem 0;
  padding: 1.5rem;
  background: linear-gradient(135deg, #fff3f3 0%, #ffe8e8 100%);
  border: 1px solid #ffcdd2;
  border-radius: 10px;
  box-shadow: 0 4px 12px rgba(211, 47, 47, 0.1);
}

.error-message h4 {
  color: #d32f2f;
  margin: 0 0 1rem 0;
  font-weight: 600;
}

.error-details {
  background: #ffffff;
  padding: 1.2rem;
  border-radius: 8px;
  font-size: 0.95rem;
  margin: 0;
  white-space: pre-wrap;
  word-break: break-word;
  box-shadow: inset 0 2px 4px rgba(0, 0, 0, 0.05);
  font-family: 'Monaco', 'Menlo', monospace;
  line-height: 1.5;
}

@keyframes spin {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}

@keyframes fadeIn {
  from { opacity: 0; transform: translateY(-10px); }
  to { opacity: 1; transform: translateY(0); }
}

/* 添加滚动条样式 */
.log-content::-webkit-scrollbar,
.error-details::-webkit-scrollbar {
  width: 8px;
}

.log-content::-webkit-scrollbar-track,
.error-details::-webkit-scrollbar-track {
  background: #f1f1f1;
  border-radius: 4px;
}

.log-content::-webkit-scrollbar-thumb,
.error-details::-webkit-scrollbar-thumb {
  background: #c1c1c1;
  border-radius: 4px;
}

.log-content::-webkit-scrollbar-thumb:hover,
.error-details::-webkit-scrollbar-thumb:hover {
  background: #a8a8a8;
}

/* 添加文件输入框样式 */
input[type="file"] {
  width: 100%;
  padding: 0.8rem;
  border: 2px dashed #e2e8f0;
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.3s ease;
}

input[type="file"]:hover {
  border-color: #42b983;
  background: rgba(66, 185, 131, 0.05);
}

input[type="file"]:disabled {
  border-color: #e2e8f0;
  background: #f8fafc;
  cursor: not-allowed;
}

/* 响应式布局调整 */
@media (max-width: 1024px) {
  .main-content {
    grid-template-columns: 1fr;  /* 小屏幕时切换为单列 */
  }
  
  .video-section {
    position: relative;
    top: 0;
  }
}
</style>