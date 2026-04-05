<template>
  <div class="app-container">
    <!-- 背景网格 -->
    <div class="grid-background"></div>
    
    <div class="content-wrapper">
      <!-- 头部 -->
      <div class="header-section">
        <div class="brand-box">
          <div class="logo-icon">
            <el-icon><Position /></el-icon>
          </div>
          <div class="brand-text">
            <h1>极速快递</h1>
            <p>{{ expiryMinutes }}分钟阅后即焚 · 安全传输</p>
          </div>
        </div>
      </div>

      <div class="main-card">
        <!-- 结果展示区域 (优先级最高，有结果时显示) -->
        <transition name="el-zoom-in-top">
          <div v-if="shareInfo" class="result-panel">
            <div class="success-header">
              <div class="success-icon">
                <el-icon><CircleCheckFilled /></el-icon>
              </div>
              <h3>{{ shareInfo.filename ? '文件' : '文本' }}已封装</h3>
              <p>请在下方复制取件码链接</p>
            </div>

            <div class="info-card-bordered">
              <div class="info-row">
                <span class="label">类型</span>
                <span class="value">{{ shareInfo.filename ? '文件' : '纯文本' }}</span>
              </div>
              <div class="info-row" v-if="shareInfo.filename">
                <span class="label">文件名</span>
                <span class="value text-truncate">{{ shareInfo.filename }}</span>
              </div>
              <div class="info-row">
                <span class="label">大小</span>
                <span class="value">{{ formatFileSize(shareInfo.size) }}</span>
              </div>
              <div class="info-row">
                <span class="label warning-text">销毁倒计时</span>
                <span class="value countdown-text">{{ remainingTime }}</span>
              </div>
            </div>

            <div class="link-section">
              <div class="input-with-button">
                <el-input
                  v-model="shareLink"
                  readonly
                  class="link-input"
                >
                  <template #prefix>
                    <el-icon><Link /></el-icon>
                  </template>
                </el-input>
                <el-button type="primary" class="copy-btn" @click="copyLink">
                  复制链接
                </el-button>
              </div>
              
              <!-- 二维码区域 -->
              <div class="qr-code-area">
                <div class="qr-code-box">
                  <canvas ref="qrcodeCanvas"></canvas>
                </div>
                <div class="qr-tip">扫码查看</div>
              </div>
            </div>

            <div class="action-footer">
              <el-button @click="reset">
                <el-icon><RefreshRight /></el-icon> 继续分享
              </el-button>
              <el-button @click="openLink">
                <el-icon><View /></el-icon> 打开链接
              </el-button>
              <el-button v-if="shareInfo.filename" @click="downloadFile">
                <el-icon><Download /></el-icon> 下载文件
              </el-button>
              <el-button v-else @click="viewContent">
                <el-icon><View /></el-icon> 查看内容
              </el-button>
            </div>
          </div>

          <!-- 输入区域 (无结果时显示) -->
          <div v-else class="input-panel">
            <el-tabs v-model="activeTab" class="custom-tabs">
              <!-- 文本标签页 -->
              <el-tab-pane label="分享文本" name="text">
                <template #label>
                  <span class="tab-label">
                    <el-icon><ChatLineSquare /></el-icon> 分享文本
                  </span>
                </template>
                
                <div class="tab-content">
                  <el-input
                    v-model="textContent"
                    type="textarea"
                    :rows="8"
                    placeholder="在此粘贴代码、链接或私密笔记..."
                    resize="none"
                    class="mono-textarea"
                    maxlength="50000"
                    show-word-limit
                  />
                  <div class="tab-footer">
                    <el-button 
                      type="primary" 
                      color="#333" 
                      :loading="uploading"
                      :disabled="!textContent.trim()"
                      @click="shareText"
                      class="submit-btn"
                    >
                      <el-icon><Promotion /></el-icon> 生成链接
                    </el-button>
                  </div>
                </div>
              </el-tab-pane>

              <!-- 文件标签页 -->
              <el-tab-pane label="分享文件" name="file">
                <template #label>
                  <span class="tab-label">
                    <el-icon><Folder /></el-icon> 分享文件
                  </span>
                </template>

                <div class="tab-content">
                  <el-upload
                    ref="uploadRef"
                    class="border-upload"
                    drag
                    :auto-upload="false"
                    :on-change="handleFileChange"
                    :limit="1"
                    :show-file-list="false"
                  >
                    <div class="upload-placeholder">
                      <div class="icon-circle">
                        <el-icon><UploadFilled /></el-icon>
                      </div>
                      <div class="upload-texts">
                        <h4>点击或拖拽文件至此</h4>
                        <p>最大支持 5MB，不限格式</p>
                      </div>
                    </div>
                  </el-upload>

                  <!-- 文件选中状态 -->
                  <transition name="el-fade-in">
                    <div v-if="selectedFile" class="file-preview-item">
                      <div class="file-icon">
                        <el-icon><Document /></el-icon>
                      </div>
                      <div class="file-info-text">
                        <div class="name">{{ selectedFile.name }}</div>
                        <div class="size">{{ formatFileSize(selectedFile.size) }}</div>
                      </div>
                      <el-button 
                        type="primary" 
                        color="#333" 
                        size="small"
                        class="upload-btn-mini"
                        :loading="uploading"
                        @click="uploadFile"
                      >
                        上传
                      </el-button>
                    </div>
                  </transition>
                </div>
              </el-tab-pane>
            </el-tabs>
          </div>
        </transition>
      </div>

      <!-- 说明卡片 -->
      <div class="tips-card-bordered">
        <div class="tips-header">
          <el-icon><InfoFilled /></el-icon> 使用须知
        </div>
        <div class="tips-grid">
          <div class="tip-point">
            <span class="dot"></span>
            <span>有效期 {{ expiryMinutes }} 分钟</span>
          </div>
          <div class="tip-point">
            <span class="dot"></span>
            <span>过期后数据物理删除</span>
          </div>
          <div class="tip-point">
            <span class="dot"></span>
            <span>禁止传播违法违规内容</span>
          </div>
        </div>
      </div>

      <!-- 管理员查看所有分享 -->
      <div v-if="isAdmin" class="admin-section">
        <div class="section-header">
          <h3>
            <el-icon><Folder /></el-icon>
            所有分享记录
          </h3>
          <el-button text @click="loadAllShares">
            <el-icon><RefreshRight /></el-icon>
            刷新
          </el-button>
        </div>

        <div v-if="allShares.length === 0" class="empty-state">
          <el-icon class="empty-icon"><FolderOpened /></el-icon>
          <p>暂无分享记录</p>
        </div>

        <div v-else class="shares-list">
          <div v-for="share in allShares" :key="share.file_id" class="share-item">
            <div class="share-main">
              <div class="share-icon">
                <el-icon><Document /></el-icon>
              </div>
              <div class="share-details">
                <div class="share-name">{{ share.filename }}</div>
                <div class="share-meta">
                  <span><el-icon><User /></el-icon>{{ share.username }}</span>
                  <span>{{ formatFileSize(share.size) }}</span>
                  <span>{{ share.created_at }}</span>
                </div>
              </div>
              <div class="share-status">
                <el-tag v-if="share.is_expired" type="info" size="small">已过期</el-tag>
                <el-tag v-else type="success" size="small">
                  {{ Math.floor(share.remaining_seconds / 60) }}:{{ String(share.remaining_seconds % 60).padStart(2, '0') }}
                </el-tag>
              </div>
            </div>
            <div class="share-actions">
              <el-button text size="small" @click="viewShare(share.file_id)">
                <el-icon><View /></el-icon>
                查看
              </el-button>
              <el-button text size="small" @click="copyShareLink(share.share_url)">
                <el-icon><Link /></el-icon>
                复制
              </el-button>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onUnmounted, nextTick, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import QRCode from 'qrcode'
import {
  Position,
  ChatLineSquare,
  Folder,
  UploadFilled,
  Document,
  Link,
  CircleCheckFilled,
  Download,
  View,
  RefreshRight,
  InfoFilled,
  Promotion,
  FolderOpened,
  User
} from '@element-plus/icons-vue'
import api from '../api'

// 状态
const activeTab = ref('text')
const uploadRef = ref(null)
const textContent = ref('')
const selectedFile = ref(null)
const uploading = ref(false)
const shareInfo = ref(null)
const shareLink = ref('')
const remainingTime = ref('')
const qrcodeCanvas = ref(null)
const isAdmin = ref(localStorage.getItem('role') === 'admin')
const allShares = ref([])
const expiryMinutes = ref(2) // 默认2分钟，从后端获取
let countdownTimer = null

// 加载配置
const loadConfig = async () => {
  try {
    const { data } = await api.get('/file-share/config')
    expiryMinutes.value = data.expiry_minutes
  } catch (error) {
    console.error('加载配置失败:', error)
  }
}

// 逻辑
const shareText = async () => {
  if (!textContent.value.trim()) return
  uploading.value = true
  try {
    const blob = new Blob([textContent.value], { type: 'text/plain;charset=utf-8' })
    const file = new File([blob], 'shared_text.txt', { type: 'text/plain' })
    const formData = new FormData()
    formData.append('file', file)

    const username = localStorage.getItem('username')
    const url = username ? `/file-share/upload?username=${encodeURIComponent(username)}` : '/file-share/upload'

    const { data } = await api.post(url, formData, {
      headers: { 'Content-Type': 'multipart/form-data' }
    })

    handleSuccess(data)
    ElMessage.success('文本已封装')
  } catch (error) {
    ElMessage.error(error.response?.data?.detail || '分享失败')
  } finally {
    uploading.value = false
  }
}

const handleFileChange = (file) => {
  if (file.size > 5 * 1024 * 1024) {
    ElMessage.error('文件大小不能超过 5MB')
    return
  }
  selectedFile.value = file.raw
}

const uploadFile = async () => {
  if (!selectedFile.value) return
  uploading.value = true
  try {
    const formData = new FormData()
    formData.append('file', selectedFile.value)
    
    const username = localStorage.getItem('username')
    const url = username ? `/file-share/upload?username=${encodeURIComponent(username)}` : '/file-share/upload'
    
    const { data } = await api.post(url, formData, {
      headers: { 'Content-Type': 'multipart/form-data' }
    })

    handleSuccess(data)
    ElMessage.success('文件已封装')
  } catch (error) {
    ElMessage.error(error.response?.data?.detail || '上传失败')
  } finally {
    uploading.value = false
  }
}

const handleSuccess = (data) => {
  shareInfo.value = data
  shareLink.value = `${window.location.origin}/share/${data.file_id}`
  startCountdown()
  // 生成二维码
  nextTick(() => {
    generateQRCode()
  })
}

const generateQRCode = async () => {
  if (!qrcodeCanvas.value || !shareLink.value) return
  
  try {
    await QRCode.toCanvas(qrcodeCanvas.value, shareLink.value, {
      width: 160,
      margin: 1,
      color: {
        dark: '#000000',
        light: '#FFFFFF'
      }
    })
  } catch (error) {
    console.error('生成二维码失败:', error)
  }
}

const startCountdown = () => {
  if (countdownTimer) clearInterval(countdownTimer)
  
  const update = () => {
    if (!shareInfo.value) return
    const diff = new Date(shareInfo.value.expire_at).getTime() - Date.now()
    if (diff <= 0) {
      remainingTime.value = '已过期'
      clearInterval(countdownTimer)
      return
    }
    const mins = Math.floor(diff / 60000)
    const secs = Math.floor((diff % 60000) / 1000)
    remainingTime.value = `${mins}分 ${secs}秒`
  }
  update()
  countdownTimer = setInterval(update, 1000)
}

const copyLink = async () => {
  try {
    await navigator.clipboard.writeText(shareLink.value)
    ElMessage.success('链接已复制')
  } catch {
    ElMessage.error('复制失败')
  }
}

const openLink = () => {
  window.open(shareLink.value, '_blank')
}

const viewContent = () => window.open(shareLink.value, '_blank')
const downloadFile = () => window.open(shareLink.value, '_blank')

const reset = () => {
  textContent.value = ''
  selectedFile.value = null
  shareInfo.value = null
  shareLink.value = ''
  remainingTime.value = ''
  if (countdownTimer) clearInterval(countdownTimer)
  if (uploadRef.value) uploadRef.value.clearFiles()
}

const formatFileSize = (bytes) => {
  if (bytes === 0) return '0 B'
  const k = 1024
  const sizes = ['B', 'KB', 'MB', 'GB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  return (bytes / Math.pow(k, i)).toFixed(2) + ' ' + sizes[i]
}

// 管理员功能
const loadAllShares = async () => {
  try {
    const { data } = await api.get('/file-share/admin/list')
    allShares.value = data.shares || []
  } catch (error) {
    ElMessage.error(error.response?.data?.detail || '加载失败')
  }
}

const viewShare = (fileId) => {
  const url = `${window.location.origin}/share/${fileId}`
  window.open(url, '_blank')
}

const copyShareLink = async (shareUrl) => {
  try {
    const fullUrl = `${window.location.origin}${shareUrl}`
    await navigator.clipboard.writeText(fullUrl)
    ElMessage.success('链接已复制')
  } catch {
    ElMessage.error('复制失败')
  }
}

onMounted(() => {
  loadConfig()
  if (isAdmin.value) {
    loadAllShares()
  }
})

onUnmounted(() => {
  if (countdownTimer) clearInterval(countdownTimer)
})
</script>

<style scoped>
/* ---------------------------
   布局与背景
--------------------------- */
.app-container {
  position: relative;
  min-height: 100vh;
  display: flex;
  justify-content: center;
  padding: 40px 20px;
  box-sizing: border-box;
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
  color: #333;
}

/* 科技感网格背景 */
.grid-background {
  position: fixed;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background-color: #f8f9fa;
  background-image: 
    linear-gradient(#e9ecef 1px, transparent 1px),
    linear-gradient(90deg, #e9ecef 1px, transparent 1px);
  background-size: 20px 20px;
  z-index: -1;
}

.content-wrapper {
  width: 100%;
  max-width: 640px;
  display: flex;
  flex-direction: column;
  gap: 24px;
}

/* ---------------------------
   头部
--------------------------- */
.header-section {
  text-align: center;
  margin-bottom: 10px;
}

.brand-box {
  display: inline-flex;
  align-items: center;
  gap: 16px;
  padding: 10px 24px;
  background: white;
  border: 1px solid #e2e8f0;
  border-radius: 100px;
  box-shadow: 0 2px 10px rgba(0,0,0,0.03);
}

.logo-icon {
  width: 40px;
  height: 40px;
  background: #1a1a1a;
  color: white;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 20px;
}

.brand-text h1 {
  margin: 0;
  font-size: 18px;
  font-weight: 700;
  color: #1a1a1a;
  text-align: left;
}

.brand-text p {
  margin: 0;
  font-size: 12px;
  color: #666;
  text-align: left;
}

/* ---------------------------
   主卡片 (Main Card)
--------------------------- */
.main-card {
  background: white;
  border: 1px solid #dcdfe6;
  border-radius: 16px;
  box-shadow: 0 8px 30px rgba(0,0,0,0.04);
  overflow: hidden;
  transition: all 0.3s ease;
}

/* 自定义 Tabs 样式 */
.custom-tabs :deep(.el-tabs__header) {
  margin: 0;
  background: #fafafa;
  border-bottom: 1px solid #eef0f2;
}

.custom-tabs :deep(.el-tabs__nav-wrap) {
  display: flex;
  justify-content: center;
}

.custom-tabs :deep(.el-tabs__nav-wrap::after) {
  height: 0;
}

.custom-tabs :deep(.el-tabs__item) {
  height: 56px;
  font-size: 15px;
  font-weight: 500;
  color: #666;
  transition: all 0.3s;
}

.custom-tabs :deep(.el-tabs__item.is-active) {
  color: #1a1a1a;
  font-weight: 600;
  background: white;
}

.custom-tabs :deep(.el-tabs__active-bar) {
  background-color: #1a1a1a;
  height: 2px;
}

.tab-label {
  display: flex;
  align-items: center;
  gap: 6px;
}

.tab-content {
  padding: 24px;
}

/* 文本输入区 */
.mono-textarea :deep(.el-textarea__inner) {
  font-family: 'JetBrains Mono', Consolas, monospace;
  font-size: 14px;
  padding: 16px;
  border: 1px solid #e2e8f0;
  border-radius: 8px;
  background: #fdfdfd;
  box-shadow: none !important;
  transition: border 0.2s;
}

.mono-textarea :deep(.el-textarea__inner:focus) {
  border-color: #1a1a1a;
  background: white;
}

.tab-footer {
  display: flex;
  justify-content: center;
  align-items: center;
  margin-top: 16px;
  gap: 12px;
}

.hint-text {
  font-size: 12px;
  color: #999;
}

.submit-btn {
  font-weight: 600;
  padding: 10px 24px;
  border-radius: 8px;
}

/* 文件上传区 */
.border-upload :deep(.el-upload-dragger) {
  width: 100%;
  border: 2px dashed #e2e8f0;
  border-radius: 12px;
  background: #fafafa;
  padding: 40px 0;
  transition: all 0.2s;
}

.border-upload :deep(.el-upload-dragger:hover) {
  border-color: #1a1a1a;
  background: #f4f4f5;
}

.upload-placeholder {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 12px;
}

.icon-circle {
  width: 56px;
  height: 56px;
  background: white;
  border: 1px solid #e2e8f0;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 24px;
  color: #666;
}

.upload-texts h4 {
  margin: 0 0 4px;
  font-size: 15px;
  color: #333;
}

.upload-texts p {
  margin: 0;
  font-size: 12px;
  color: #999;
}

/* 文件预览项 */
.file-preview-item {
  margin-top: 16px;
  background: white;
  border: 1px solid #e2e8f0;
  border-radius: 8px;
  padding: 12px;
  display: flex;
  align-items: center;
  gap: 12px;
  box-shadow: 0 2px 8px rgba(0,0,0,0.02);
}

.file-icon {
  width: 36px;
  height: 36px;
  background: #f0f2f5;
  border-radius: 6px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #666;
}

.file-info-text {
  flex: 1;
  overflow: hidden;
}

.file-info-text .name {
  font-size: 14px;
  font-weight: 600;
  color: #333;
  margin-bottom: 2px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.file-info-text .size {
  font-size: 12px;
  color: #999;
}

.upload-btn-mini {
  border-radius: 6px;
}

/* ---------------------------
   结果面板
--------------------------- */
.result-panel {
  padding: 30px;
  text-align: center;
}

.success-header {
  margin-bottom: 24px;
}

.success-icon {
  font-size: 48px;
  color: #10b981; /* 绿色成功状态 */
  margin-bottom: 12px;
}

.success-header h3 {
  margin: 0 0 6px;
  font-size: 20px;
  color: #1a1a1a;
}

.success-header p {
  margin: 0;
  font-size: 14px;
  color: #666;
}

/* 信息卡片 */
.info-card-bordered {
  background: #f8fafc;
  border: 1px solid #e2e8f0;
  border-radius: 12px;
  padding: 16px;
  margin-bottom: 24px;
}

.info-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 8px 0;
  border-bottom: 1px dashed #e2e8f0;
  font-size: 14px;
}

.info-row:last-child {
  border-bottom: none;
}

.info-row .label {
  color: #64748b;
}

.info-row .value {
  color: #334155;
  font-weight: 600;
}

.text-truncate {
  max-width: 200px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.warning-text {
  color: #f59e0b;
}

.countdown-text {
  color: #f59e0b;
  font-family: monospace;
  font-size: 16px;
}

/* 链接区域 */
.link-section {
  margin-bottom: 24px;
}

.qr-code-area {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8px;
  margin-top: 20px;
}

.qr-code-box {
  padding: 12px;
  background: white;
  border-radius: 8px;
  border: 2px solid #e4e7ed;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.qr-code-box canvas {
  display: block;
}

.qr-tip {
  font-size: 13px;
  color: #909399;
  font-weight: 500;
}

.input-with-button {
  display: flex;
  gap: 8px;
}

.link-input :deep(.el-input__wrapper) {
  box-shadow: 0 0 0 1px #e2e8f0 inset;
}

.link-input :deep(.el-input__inner) {
  color: #334155;
  font-weight: 500;
}

.copy-btn {
  background: #1a1a1a;
  border-color: #1a1a1a;
  font-weight: 600;
}

.copy-btn:hover {
  background: #333;
  border-color: #333;
}

.action-footer {
  display: flex;
  justify-content: center;
  gap: 12px;
}

/* ---------------------------
   底部说明卡片
--------------------------- */
.tips-card-bordered {
  background: white;
  border: 1px solid #e2e8f0;
  border-radius: 12px;
  padding: 16px 20px;
}

.tips-header {
  font-size: 14px;
  font-weight: 600;
  color: #666;
  margin-bottom: 12px;
  display: flex;
  align-items: center;
  gap: 6px;
}

.tips-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 12px;
}

.tip-point {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 12px;
  color: #64748b;
}

.dot {
  width: 6px;
  height: 6px;
  background: #cbd5e1;
  border-radius: 50%;
}

/* 响应式 */
@media (max-width: 600px) {
  .app-container {
    padding: 20px 10px;
  }
  
  .tips-grid {
    grid-template-columns: 1fr;
  }
  
  .action-footer {
    flex-direction: column;
  }
  
  .action-footer .el-button {
    width: 100%;
    margin: 0;
  }
}

/* 移动端适配 */
@media (max-width: 768px) {
  .link-qr-container {
    flex-direction: column;
    align-items: stretch;
  }

  .qr-code-area {
    margin-top: 16px;
    padding: 16px;
    background: #f5f7fa;
    border-radius: 8px;
  }

  .qr-code-box {
    margin: 0 auto;
  }
}

/* ---------------------------
   管理员面板
--------------------------- */
.admin-section {
  background: white;
  border: 1px solid #e2e8f0;
  border-radius: 12px;
  padding: 20px;
  box-shadow: 0 2px 8px rgba(0,0,0,0.04);
}

.section-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
  padding-bottom: 16px;
  border-bottom: 1px solid #f0f2f5;
}

.section-header h3 {
  margin: 0;
  font-size: 16px;
  font-weight: 600;
  color: #333;
  display: flex;
  align-items: center;
  gap: 8px;
}

.empty-state {
  text-align: center;
  padding: 60px 20px;
  color: #909399;
}

.empty-icon {
  font-size: 64px;
  color: #dcdfe6;
  margin-bottom: 16px;
}

.empty-state p {
  margin: 0;
  font-size: 14px;
}

.shares-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.share-item {
  background: #fafafa;
  border: 1px solid #e2e8f0;
  border-radius: 8px;
  padding: 16px;
  transition: all 0.2s;
}

.share-item:hover {
  background: #f5f7fa;
  border-color: #d0d7de;
}

.share-main {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 12px;
}

.share-icon {
  width: 36px;
  height: 36px;
  background: white;
  border: 1px solid #e2e8f0;
  border-radius: 6px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 18px;
  color: #666;
  flex-shrink: 0;
}

.share-details {
  flex: 1;
  min-width: 0;
}

.share-name {
  font-size: 14px;
  font-weight: 600;
  color: #333;
  margin-bottom: 4px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.share-meta {
  display: flex;
  gap: 12px;
  font-size: 12px;
  color: #666;
}

.share-meta span {
  display: flex;
  align-items: center;
  gap: 4px;
}

.share-meta .el-icon {
  font-size: 12px;
}

.share-status {
  flex-shrink: 0;
}

.share-actions {
  display: flex;
  gap: 8px;
  padding-top: 12px;
  border-top: 1px solid #e2e8f0;
}

.share-actions .el-button {
  flex: 1;
}

/* 响应式 */
@media (max-width: 768px) {
  .share-main {
    flex-wrap: wrap;
  }
  
  .share-status {
    width: 100%;
    margin-top: 8px;
  }
  
  .share-meta {
    flex-direction: column;
    gap: 4px;
  }
}
</style>