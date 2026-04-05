<template>
  <div class="app-container" :class="{ dark: theme === 'dark' }">
    <!-- 背景网格 -->
    <div class="grid-background"></div>
    <div v-if="theme === 'dark'" class="meteor-layer">
      <span class="meteor meteor-1"></span>
      <span class="meteor meteor-2"></span>
      <span class="meteor meteor-3"></span>
    </div>

    <div class="content-wrapper">
      <!-- 头部品牌 -->
      <div class="header-section">
        <div class="brand-box">
          <div class="logo-icon">
            <el-icon><Box /></el-icon>
          </div>
          <div class="brand-text">
            <h1>极速取件</h1>
            <p>安全传输 · 阅后即焚</p>
          </div>
        </div>
      </div>

      <div class="main-card">
        <!-- 1. 加载中状态 -->
        <div v-if="loading" class="status-panel loading-panel">
          <el-icon class="is-loading spinner-icon"><Loading /></el-icon>
          <p>正在解析取件码...</p>
        </div>

        <!-- 2. 文件/文本详情状态 -->
        <div v-else-if="fileInfo && !expired" class="content-panel">
          <div class="panel-header">
            <div class="file-type-icon">
              <el-icon><Document /></el-icon>
            </div>
            <div class="header-info">
              <h2>{{ isTextFile ? '文本内容已就绪' : '文件准备就绪' }}</h2>
              <p>请在 <span class="countdown">{{ remainingTime }}</span> 内查收</p>
            </div>
          </div>

          <!-- 信息概览卡片 -->
          <div class="meta-card">
            <div class="meta-row">
              <span class="label">名称</span>
              <span class="value filename" :title="fileInfo.filename">{{ fileInfo.filename || '未知文件名' }}</span>
            </div>
            <div class="meta-row">
              <span class="label">大小</span>
              <span class="value">{{ formatFileSize(fileInfo.size) }}</span>
            </div>
            <div class="meta-row">
              <span class="label">类型</span>
              <span class="value tag">{{ isTextFile ? '纯文本' : '二进制文件' }}</span>
            </div>
          </div>

          <!-- 文本预览区域 -->
          <div v-if="isTextFile && textContent" class="preview-section">
            <div class="preview-toolbar">
              <span class="toolbar-title"><el-icon><View /></el-icon> 内容预览</span>
              <el-button size="small" text bg @click="copyText">
                <el-icon><CopyDocument /></el-icon> 复制
              </el-button>
            </div>
            <div class="code-block">
              <pre>{{ textContent }}</pre>
            </div>
          </div>

          <!-- 操作按钮组 -->
          <div class="action-footer">
            <!-- 纯文本：只显示复制文本按钮 -->
            <template v-if="isTextFile && textContent">
              <el-button 
                type="primary" 
                class="primary-btn" 
                size="large" 
                @click="copyText"
              >
                <el-icon><CopyDocument /></el-icon> 
                复制文本内容
              </el-button>
              <el-button class="secondary-btn" size="large" @click="copyLink">
                <el-icon><Link /></el-icon> 复制链接
              </el-button>
            </template>
            
            <!-- 文件：显示下载按钮 -->
            <template v-else>
              <el-button 
                type="primary" 
                class="primary-btn" 
                size="large" 
                @click="downloadFile"
              >
                <el-icon><Download /></el-icon> 
                立即下载
              </el-button>
              <el-button class="secondary-btn" size="large" @click="copyLink">
                <el-icon><Link /></el-icon> 复制链接
              </el-button>
            </template>
          </div>
        </div>

        <!-- 3. 已过期状态 -->
        <div v-else-if="expired" class="status-panel expired-panel">
          <div class="status-icon warning">
            <el-icon><WarningFilled /></el-icon>
          </div>
          <h3>内容已销毁</h3>
          <p>该分享已超过 2 分钟有效期或已被删除</p>
          <el-button type="primary" class="primary-btn" @click="goToShare">
            我也要发件
          </el-button>
        </div>

        <!-- 4. 错误状态 -->
        <div v-else-if="error" class="status-panel error-panel">
          <div class="status-icon error">
            <el-icon><CircleCloseFilled /></el-icon>
          </div>
          <h3>无法获取内容</h3>
          <p>{{ error }}</p>
          <el-button @click="loadFileInfo">刷新重试</el-button>
        </div>
      </div>

      <!-- 底部说明 -->
      <div class="footer-tips">
        <el-icon><Lock /></el-icon>
        <span>端对端加密传输 · 限时后物理删除</span>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed, ref, onMounted, onUnmounted, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import {
  Box,
  Document,
  Loading,
  Download,
  Link,
  CopyDocument,
  View,
  WarningFilled,
  CircleCloseFilled,
  Lock
} from '@element-plus/icons-vue'
import { fetchParcelMeta, pickupParcel } from '../lib/api'

const route = useRoute()
const router = useRouter()

const loading = ref(true)
const theme = ref((route.query.theme || localStorage.getItem('pickup-theme') || 'light').toString())
const fileInfo = ref(null)
const textContent = ref('')
const downloadUrl = ref('')
const expired = ref(false)
const error = ref('')
const remainingTime = ref('')
const isTextFile = ref(false)
let countdownTimer = null

const code = computed(() => (route.params.code || '').toString().toUpperCase())

const loadFileInfo = async () => {
  loading.value = true
  error.value = ''
  expired.value = false
  textContent.value = ''
  downloadUrl.value = ''
  fileInfo.value = null

  try {
    if (!code.value) {
      error.value = '缺少取件码'
      return
    }

    const meta = await fetchParcelMeta(code.value)
    const data = await pickupParcel({ code: code.value })
    const firstFile = data.files[0]
    const textSize = data.text_content ? new TextEncoder().encode(data.text_content).length : 0

    fileInfo.value = {
      filename: firstFile?.original_name || `${data.code}.txt`,
      size: firstFile?.size || textSize,
      remaining_seconds: Math.max(0, Math.floor((new Date(data.expires_at).getTime() - Date.now()) / 1000))
    }

    textContent.value = data.text_content || ''
    downloadUrl.value = firstFile?.download_url || ''
    isTextFile.value = !firstFile && !!data.text_content
    expired.value = meta.is_expired
    startCountdown()
  } catch (err) {
    const message = err.message || '取件码无效或网络错误'
    if (message.includes('expired') || message.includes('not found') || message.includes('Parcel')) {
      expired.value = true
    } else {
      error.value = message
    }
  } finally {
    loading.value = false
  }
}

const startCountdown = () => {
  if (countdownTimer) {
    clearInterval(countdownTimer)
  }

  const updateCountdown = () => {
    if (!fileInfo.value) return

    // 先递减
    fileInfo.value.remaining_seconds--
    let remaining = fileInfo.value.remaining_seconds
    
    if (remaining <= 0) {
      remainingTime.value = '已过期'
      expired.value = true
      clearInterval(countdownTimer)
      return
    }
    
    const minutes = Math.floor(remaining / 60)
    const seconds = remaining % 60
    remainingTime.value = `${minutes}分 ${seconds}秒`
  }

  // 先显示初始时间
  if (fileInfo.value.remaining_seconds <= 0) {
    expired.value = true
    return
  }
  
  const minutes = Math.floor(fileInfo.value.remaining_seconds / 60)
  const seconds = fileInfo.value.remaining_seconds % 60
  remainingTime.value = `${minutes}分 ${seconds}秒`
  
  countdownTimer = setInterval(updateCountdown, 1000)
}

const downloadFile = () => {
  if (downloadUrl.value) {
    window.open(downloadUrl.value, '_blank')
  }
}

const copyLink = async () => {
  try {
    const link = window.location.href
    await navigator.clipboard.writeText(link)
    ElMessage.success('链接已复制')
  } catch (error) {
    ElMessage.error('复制失败')
  }
}

const copyText = async () => {
  try {
    await navigator.clipboard.writeText(textContent.value)
    ElMessage.success('内容已复制')
  } catch (error) {
    ElMessage.error('复制失败')
  }
}

const goToShare = () => {
  router.push('/')
}

const formatFileSize = (bytes) => {
  if (bytes === 0) return '0 B'
  const k = 1024
  const sizes = ['B', 'KB', 'MB', 'GB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  return Math.round(bytes / Math.pow(k, i) * 100) / 100 + ' ' + sizes[i]
}

onMounted(() => {
  localStorage.setItem('pickup-theme', theme.value)
  loadFileInfo()
})

watch(code, () => {
  loadFileInfo()
})

watch(
  () => route.query.theme,
  (value) => {
    if (value) {
      theme.value = value.toString()
      localStorage.setItem('pickup-theme', theme.value)
    }
  }
)

onUnmounted(() => {
  if (countdownTimer) {
    clearInterval(countdownTimer)
  }
})
</script>

<style scoped>
/* ---------------------------
   布局与背景 (与 Share 页面统一)
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
  overflow: hidden;
}

.app-container > *:not(.grid-background):not(.meteor-layer) {
  position: relative;
  z-index: 1;
}

.grid-background {
  position: absolute;
  inset: 0;
  background-color: #f8f9fa;
  background-image: 
    linear-gradient(#e9ecef 1px, transparent 1px),
    linear-gradient(90deg, #e9ecef 1px, transparent 1px);
  background-size: 20px 20px;
  z-index: 0;
}

.meteor-layer {
  position: absolute;
  inset: 0;
  z-index: 0;
  pointer-events: none;
  overflow: hidden;
}

.meteor {
  position: absolute;
  width: 180px;
  height: 1px;
  background: linear-gradient(90deg, rgba(255, 255, 255, 0.95), transparent 78%);
  opacity: 0.75;
  transform: rotate(-28deg);
  box-shadow: 0 0 10px rgba(255, 255, 255, 0.35);
  animation: meteor-fall 6s linear infinite;
}

.meteor::before {
  content: "";
  position: absolute;
  right: 0;
  top: -1px;
  width: 4px;
  height: 4px;
  border-radius: 50%;
  background: #fff;
  box-shadow: 0 0 12px rgba(255, 255, 255, 0.8);
}

.meteor-1 { top: 12%; left: 66%; animation-delay: 0s; }
.meteor-2 { top: 24%; left: 82%; width: 130px; animation-delay: 2.2s; }
.meteor-3 { top: 8%; left: 78%; width: 220px; animation-delay: 4.4s; }

@keyframes meteor-fall {
  0% { opacity: 0; transform: translate3d(80px, -40px, 0) rotate(-28deg); }
  12% { opacity: 0.8; }
  100% { opacity: 0; transform: translate3d(-520px, 320px, 0) rotate(-28deg); }
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
}

.brand-text p {
  margin: 0;
  font-size: 12px;
  color: #666;
}

/* ---------------------------
   主卡片
--------------------------- */
.main-card {
  background: white;
  border: 1px solid #dcdfe6;
  border-radius: 16px;
  box-shadow: 0 8px 30px rgba(0,0,0,0.04);
  overflow: hidden;
  transition: all 0.3s ease;
}

/* 状态面板通用样式 */
.status-panel {
  padding: 40px 20px;
  text-align: center;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  min-height: 300px;
}

/* 加载中 */
.spinner-icon {
  font-size: 40px;
  color: #409eff;
  margin-bottom: 16px;
}

.loading-panel p {
  color: #666;
  font-size: 14px;
}

/* 过期/错误 */
.status-icon {
  font-size: 48px;
  margin-bottom: 16px;
}

.status-icon.warning { color: #f59e0b; }
.status-icon.error { color: #f56c6c; }

.status-panel h3 {
  margin: 0 0 8px;
  font-size: 18px;
  color: #1a1a1a;
}

.status-panel p {
  margin: 0 0 24px;
  color: #666;
  font-size: 14px;
}

/* ---------------------------
   内容展示面板 (Content Panel)
--------------------------- */
.content-panel {
  padding: 30px;
}

.panel-header {
  display: flex;
  align-items: center;
  gap: 16px;
  margin-bottom: 24px;
  padding-bottom: 20px;
  border-bottom: 1px solid #f0f2f5;
}

.file-type-icon {
  width: 48px;
  height: 48px;
  background: #f0f2f5;
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 24px;
  color: #1a1a1a;
}

.header-info h2 {
  margin: 0 0 4px;
  font-size: 18px;
  color: #1a1a1a;
}

.header-info p {
  margin: 0;
  font-size: 13px;
  color: #666;
}

.countdown {
  color: #f59e0b;
  font-weight: 600;
  font-family: monospace;
}

/* 元数据卡片 */
.meta-card {
  background: #f8fafc;
  border: 1px solid #e2e8f0;
  border-radius: 8px;
  padding: 16px;
  margin-bottom: 24px;
}

.meta-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
  font-size: 14px;
}

.meta-row:last-child {
  margin-bottom: 0;
}

.meta-row .label {
  color: #64748b;
  min-width: 60px;
}

.meta-row .value {
  color: #334155;
  font-weight: 600;
  text-align: right;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  max-width: 200px;
}

.meta-row .value.tag {
  background: #e2e8f0;
  padding: 2px 8px;
  border-radius: 4px;
  font-size: 12px;
}

/* 文本预览 */
.preview-section {
  margin-bottom: 24px;
  border: 1px solid #e2e8f0;
  border-radius: 8px;
  overflow: hidden;
}

.preview-toolbar {
  background: #f8fafc;
  padding: 8px 12px;
  display: flex;
  justify-content: space-between;
  align-items: center;
  border-bottom: 1px solid #e2e8f0;
}

.toolbar-title {
  font-size: 12px;
  font-weight: 600;
  color: #64748b;
  display: flex;
  align-items: center;
  gap: 6px;
}

.code-block {
  background: white;
  padding: 16px;
  max-height: 300px;
  overflow-y: auto;
}

.code-block pre {
  margin: 0;
  font-family: 'JetBrains Mono', Consolas, monospace;
  font-size: 13px;
  line-height: 1.6;
  color: #334155;
  white-space: pre-wrap;
  word-wrap: break-word;
}

/* 操作按钮 */
.action-footer {
  display: flex;
  gap: 12px;
}

.action-footer .el-button {
  flex: 1;
}

.primary-btn {
  background: #1a1a1a;
  border-color: #1a1a1a;
  font-weight: 600;
}

.primary-btn:hover {
  background: #333;
  border-color: #333;
}

.secondary-btn {
  font-weight: 600;
}

/* ---------------------------
   底部说明
--------------------------- */
.footer-tips {
  text-align: center;
  font-size: 12px;
  color: #94a3b8;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 6px;
}

.app-container.dark {
  color: #e5e7eb;
}

.app-container.dark .grid-background {
  background-color: #0b0d10;
  background-image:
    linear-gradient(rgba(255, 255, 255, 0.08) 1px, transparent 1px),
    linear-gradient(90deg, rgba(255, 255, 255, 0.08) 1px, transparent 1px);
}

.app-container.dark::before {
  content: "";
  position: absolute;
  inset: 0;
  z-index: 0;
  pointer-events: none;
  background:
    radial-gradient(circle at top center, rgba(255, 255, 255, 0.04), transparent 30%),
    linear-gradient(180deg, rgba(255, 255, 255, 0.02), transparent 40%);
}

.app-container.dark .brand-box,
.app-container.dark .main-card,
.app-container.dark .meta-card,
.app-container.dark .preview-section,
.app-container.dark .preview-toolbar,
.app-container.dark .code-block {
  background: #181b1f;
  border-color: #343a40;
  color: #e5e7eb;
  box-shadow: none;
}

.app-container.dark .logo-icon {
  background: #f3f4f6;
  color: #111;
}

.app-container.dark .brand-text h1,
.app-container.dark .status-panel h3,
.app-container.dark .header-info h2,
.app-container.dark .meta-row .value,
.app-container.dark .code-block pre {
  color: #f9fafb;
}

.app-container.dark .brand-text p,
.app-container.dark .status-panel p,
.app-container.dark .header-info p,
.app-container.dark .meta-row .label,
.app-container.dark .toolbar-title,
.app-container.dark .footer-tips {
  color: #9ca3af;
}

.app-container.dark .file-type-icon,
.app-container.dark .meta-row .value.tag {
  background: #111315;
  color: #f3f4f6;
}

.app-container.dark .panel-header {
  border-bottom-color: #343a40;
}

.app-container.dark .secondary-btn {
  background: #20242a !important;
  border-color: #343a40 !important;
  color: #f3f4f6 !important;
}

/* 响应式 */
@media (max-width: 600px) {
  .app-container {
    padding: 20px 10px;
  }
}
</style>
