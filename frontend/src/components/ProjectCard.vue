<!-- AIMETA P=项目卡片_小说项目展示|R=项目信息卡片|NR=不含编辑功能|E=component:ProjectCard|X=internal|A=卡片组件|D=vue|S=dom|RD=./README.ai -->
<template>
  <div class="novel-card" @click="$emit('detail', project.id)">
    <!-- Delete Icon Button -->
    <button class="delete-btn" @click.stop="handleDelete" title="删除项目">
      <svg class="w-4 h-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
        <path stroke-linecap="round" stroke-linejoin="round" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
      </svg>
    </button>

    <!-- Cover Section - Full Height (Display Only) -->
    <div class="cover-section">
      <img 
        v-if="project.cover_url" 
        :src="coverImageSrc" 
        :alt="project.title"
        class="cover-image"
      />
      <div v-else class="cover-placeholder">
        <svg
          class="placeholder-icon"
          viewBox="0 0 24 24"
          fill="none"
          stroke="currentColor"
          stroke-width="1.5"
        >
          <path stroke-linecap="round" stroke-linejoin="round" d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z" />
        </svg>
        <span class="placeholder-text">无封面</span>
      </div>
    </div>

    <!-- Content Section -->
    <div class="content-section">
      <!-- Title and Status -->
      <div class="header-section">
        <h3 class="card-title">{{ project.title }}</h3>
        <div class="meta-line">
          <span class="status-badge">{{ getStatusText }}</span>
          <span class="time-text">{{ formatRelativeTime(project.last_edited) }}</span>
        </div>
      </div>



      <!-- Progress Bar -->
      <div class="progress-section">
        <div class="progress-header">
          <span class="progress-label">完成度</span>
          <span class="progress-value">{{ progress }}%</span>
        </div>
        <div class="progress-track">
          <div class="progress-fill" :style="{ width: `${progress}%` }"></div>
        </div>
      </div>

      <!-- Action Buttons -->
      <div class="action-buttons">
        <button class="view-btn" @click.stop="$emit('detail', project.id)">
          <svg class="w-4 h-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path stroke-linecap="round" stroke-linejoin="round" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
            <path stroke-linecap="round" stroke-linejoin="round" d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z" />
          </svg>
          查看
        </button>
        <button class="create-btn" @click.stop="$emit('continue', project)">
          <svg class="w-4 h-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path stroke-linecap="round" stroke-linejoin="round" d="M15.232 5.232l3.536 3.536m-2.036-5.036a2.5 2.5 0 113.536 3.536L6.5 21.036H3v-3.572L16.732 3.732z" />
          </svg>
          创作
        </button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import type { NovelProjectSummary } from '@/api/novel'
import { formatRelativeTime } from '@/utils/date'

interface Props {
  project: NovelProjectSummary
}

const props = defineProps<Props>()

const emit = defineEmits<{
  (e: 'click', id: string): void
  (e: 'detail', id: string): void
  (e: 'continue', project: NovelProjectSummary): void
  (e: 'delete', id: string): void
  (e: 'coverGenerated', data: { id: string, cover_url: string }): void
}>()

const coverImageSrc = computed(() => {
  const url = props.project.cover_url
  if (!url) return ''
  if (url.startsWith('http') || url.startsWith('/')) return url
  return `/${url}`
})

const progress = computed(() => {
  const { completed_chapters, total_chapters } = props.project
  return total_chapters > 0 ? Math.round((completed_chapters / total_chapters) * 100) : 0
})

const getStatusText = computed(() => {
  const { completed_chapters, total_chapters } = props.project
  if (total_chapters === 0) return '蓝图'
  if (completed_chapters >= total_chapters) return '完结'
  return '连载中'
})

const handleDelete = () => {
  emit('delete', props.project.id)
}
</script>

<style scoped>
.novel-card {
  position: relative;
  display: flex;
  background: #ffffff;
  border-radius: 16px;
  overflow: hidden;
  border: 1px solid rgba(0, 0, 0, 0.08);
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  cursor: pointer;
  height: 200px;
}

.novel-card:hover {
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.08), 0 2px 6px rgba(0, 0, 0, 0.04);
  border-color: rgba(0, 0, 0, 0.12);
  transform: translateY(-2px);
}

/* Delete Button */
.delete-btn {
  position: absolute;
  top: 12px;
  right: 12px;
  width: 36px;
  height: 36px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: rgba(255, 255, 255, 0.98);
  border: none;
  border-radius: 50%;
  color: #d32f2f;
  opacity: 0;
  transition: all 0.25s cubic-bezier(0.4, 0, 0.2, 1);
  cursor: pointer;
  z-index: 10;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.15);
}

.novel-card:hover .delete-btn {
  opacity: 1;
}

.delete-btn:hover {
  background: #fdecea;
  transform: scale(1.08);
}

.delete-btn:active {
  transform: scale(0.96);
}

/* Cover Section - Full Height */
.cover-section {
  position: relative;
  flex-shrink: 0;
  width: 140px;
  height: 100%;
  background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%);
  overflow: hidden;
}

.cover-image {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.cover-placeholder {
  width: 100%;
  height: 100%;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 8px;
  color: #9e9e9e;
}

.placeholder-icon {
  width: 40px;
  height: 40px;
  opacity: 0.4;
}

.placeholder-text {
  font-size: 12px;
  font-weight: 500;
  opacity: 0.6;
}



/* Content Section */
.content-section {
  flex: 1;
  padding: 20px 24px;
  display: flex;
  flex-direction: column;
  gap: 16px;
  min-width: 0;
}

/* Header */
.header-section {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.card-title {
  font-size: 18px;
  font-weight: 600;
  line-height: 1.4;
  color: #202124;
  margin: 0;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  letter-spacing: -0.02em;
}

.meta-line {
  display: flex;
  align-items: center;
  gap: 10px;
}

.status-badge {
  display: inline-flex;
  align-items: center;
  padding: 3px 10px;
  background: #e8f5e9;
  color: #2e7d32;
  border-radius: 14px;
  font-weight: 500;
  font-size: 12px;
  letter-spacing: 0.02em;
}

.time-text {
  color: #5f6368;
  font-size: 13px;
}



/* Progress */
.progress-section {
  margin-top: auto;
}

.progress-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
}

.progress-label {
  font-size: 12px;
  color: #5f6368;
  font-weight: 500;
}

.progress-value {
  font-size: 13px;
  color: #1a73e8;
  font-weight: 600;
}

.progress-track {
  width: 100%;
  height: 6px;
  background: #e8f0fe;
  border-radius: 3px;
  overflow: hidden;
}

.progress-fill {
  height: 100%;
  background: linear-gradient(90deg, #1a73e8 0%, #4285f4 100%);
  border-radius: 3px;
  transition: width 0.4s cubic-bezier(0.4, 0, 0.2, 1);
}

/* Action Buttons */
.action-buttons {
  display: flex;
  gap: 10px;
}

.view-btn,
.create-btn {
  flex: 1;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 6px;
  padding: 10px 16px;
  border: none;
  border-radius: 10px;
  font-size: 14px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
  letter-spacing: 0.02em;
}

.view-btn {
  background: #f8f9fa;
  color: #5f6368;
  border: 1px solid #dadce0;
}

.view-btn:hover {
  background: #e8eaed;
  border-color: #c4c7c5;
}

.create-btn {
  background: #1a73e8;
  color: white;
  box-shadow: 0 1px 3px rgba(26, 115, 232, 0.24);
}

.create-btn:hover {
  background: #1765cc;
  box-shadow: 0 2px 6px rgba(26, 115, 232, 0.36);
  transform: translateY(-1px);
}

.view-btn:active,
.create-btn:active {
  transform: translateY(0);
}

/* Responsive Design */
@media (max-width: 768px) {
  .novel-card {
    height: 180px;
  }
  
  .cover-section {
    width: 120px;
  }
  
  .content-section {
    padding: 16px 18px;
    gap: 14px;
  }
  
  .card-title {
    font-size: 16px;
  }
}

@media (max-width: 480px) {
  .novel-card {
    height: 160px;
  }
  
  .cover-section {
    width: 100px;
  }
  
  .content-section {
    padding: 14px 16px;
    gap: 12px;
  }
  
  .card-title {
    font-size: 15px;
  }
  
  .action-buttons {
    gap: 8px;
  }
  
  .view-btn,
  .create-btn {
    padding: 8px 12px;
    font-size: 13px;
  }
}
</style>
