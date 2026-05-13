<!-- AIMETA P=概览区_小说基本信息|R=基本信息展示|NR=不含编辑功能|E=component:OverviewSection|X=ui|A=概览组件|D=vue|S=dom|RD=./README.ai -->
<template>
  <div class="space-y-6">
    <!-- Cover Management Section (Admin Only) -->
    <div v-if="!editable" class="bg-white/95 rounded-2xl shadow-sm border border-slate-200 p-6">
      <div class="flex items-start justify-between gap-4 mb-4">
        <div>
          <h3 class="text-sm font-semibold text-indigo-600 uppercase tracking-wide">封面管理</h3>
          <p class="text-gray-500 text-xs">管理小说封面图片</p>
        </div>
      </div>
      
      <div class="flex gap-6 items-start">
        <!-- Cover Preview -->
        <div class="flex-shrink-0">
          <div class="relative w-40 h-56 rounded-lg overflow-hidden bg-gradient-to-br from-slate-100 to-slate-200 border-2 border-slate-300">
            <img 
              v-if="coverUrl" 
              :src="coverImageSrc" 
              alt="小说封面"
              class="w-full h-full object-cover"
            />
            <div v-else class="w-full h-full flex flex-col items-center justify-center text-slate-400">
              <svg class="w-12 h-12 mb-2 opacity-50" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
                <path stroke-linecap="round" stroke-linejoin="round" d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z" />
              </svg>
              <span class="text-sm">无封面</span>
            </div>
            <div v-if="isGenerating" class="absolute inset-0 bg-black/60 flex items-center justify-center backdrop-blur-sm">
              <svg class="w-10 h-10 animate-spin text-white" viewBox="0 0 24 24" fill="none">
                <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
                <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
              </svg>
            </div>
          </div>
        </div>
        
        <!-- Cover Actions -->
        <div class="flex-1 space-y-3">
          <button
            type="button"
            class="w-full px-4 py-2.5 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 transition-colors font-medium text-sm flex items-center justify-center gap-2 disabled:opacity-50 disabled:cursor-not-allowed"
            :disabled="isGenerating"
            @click="handleGenerateCover"
          >
            <svg v-if="!isGenerating" class="w-5 h-5" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path stroke-linecap="round" stroke-linejoin="round" d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z" />
            </svg>
            {{ isGenerating ? '生成中...' : (coverUrl ? '重新生成封面' : '生成 AI 封面') }}
          </button>
          
          <button
            type="button"
            class="w-full px-4 py-2.5 bg-slate-100 text-slate-700 rounded-lg hover:bg-slate-200 transition-colors font-medium text-sm flex items-center justify-center gap-2 disabled:opacity-50 disabled:cursor-not-allowed"
            :disabled="isGenerating"
            @click="triggerFileUpload"
          >
            <svg class="w-5 h-5" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path stroke-linecap="round" stroke-linejoin="round" d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-8l-4-4m0 0L8 8m4-4v12" />
            </svg>
            上传自定义封面
          </button>
          <input
            ref="fileInputRef"
            type="file"
            accept="image/*"
            class="hidden"
            @change="handleFileUpload"
          />
          
          <p class="text-xs text-slate-500 mt-2">
            建议尺寸：800x1200 像素，支持 JPG、PNG 格式
          </p>
        </div>
      </div>
    </div>

    <div class="bg-white/95 rounded-2xl shadow-sm border border-slate-200 p-6">
      <div class="flex items-start justify-between gap-4 mb-3">
        <div>
          <h3 class="text-sm font-semibold text-indigo-600 uppercase tracking-wide">核心摘要</h3>
          <p class="text-gray-500 text-xs">快速了解项目的定位与调性</p>
        </div>
        <button
          v-if="editable"
          type="button"
          class="text-gray-400 hover:text-indigo-600 transition-colors"
          @click="emitEdit('one_sentence_summary', '核心摘要', data?.one_sentence_summary)">
          <svg class="h-5 w-5" viewBox="0 0 20 20" fill="currentColor">
            <path d="M17.414 2.586a2 2 0 00-2.828 0L7 10.172V13h2.828l7.586-7.586a2 2 0 000-2.828z" />
            <path fill-rule="evenodd" d="M2 6a2 2 0 012-2h4a1 1 0 010 2H4v10h10v-4a1 1 0 112 0v4a2 2 0 01-2 2H4a2 2 0 01-2-2V6z" clip-rule="evenodd" />
          </svg>
        </button>
      </div>
      <p class="text-slate-800 text-lg leading-relaxed min-h-[2.5rem]">{{ data?.one_sentence_summary || '暂无' }}</p>
    </div>

    <div class="grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-4 gap-4">
      <div class="bg-white/95 rounded-2xl shadow-sm border border-slate-200 p-4">
        <h4 class="text-xs font-semibold text-slate-500 uppercase tracking-wide mb-2">目标受众</h4>
        <p class="text-base font-medium text-slate-800 min-h-[1.5rem]">{{ data?.target_audience || '暂无' }}</p>
      </div>
      <div class="bg-white/95 rounded-2xl shadow-sm border border-slate-200 p-4">
        <h4 class="text-xs font-semibold text-slate-500 uppercase tracking-wide mb-2">类型</h4>
        <p class="text-base font-medium text-slate-800 min-h-[1.5rem]">{{ data?.genre || '暂无' }}</p>
      </div>
      <div class="bg-white/95 rounded-2xl shadow-sm border border-slate-200 p-4">
        <h4 class="text-xs font-semibold text-slate-500 uppercase tracking-wide mb-2">风格</h4>
        <p class="text-base font-medium text-slate-800 min-h-[1.5rem]">{{ data?.style || '暂无' }}</p>
      </div>
      <div class="bg-white/95 rounded-2xl shadow-sm border border-slate-200 p-4">
        <h4 class="text-xs font-semibold text-slate-500 uppercase tracking-wide mb-2">基调</h4>
        <p class="text-base font-medium text-slate-800 min-h-[1.5rem]">{{ data?.tone || '暂无' }}</p>
      </div>
    </div>

    <div class="bg-white/95 rounded-2xl shadow-sm border border-slate-200 p-6">
      <div class="flex items-start justify-between gap-4 mb-4">
        <h3 class="text-lg font-semibold text-slate-900">完整剧情梗概</h3>
        <button
          v-if="editable"
          type="button"
          class="text-gray-400 hover:text-indigo-600 transition-colors"
          @click="emitEdit('full_synopsis', '完整剧情梗概', data?.full_synopsis)">
          <svg class="h-5 w-5" viewBox="0 0 20 20" fill="currentColor">
            <path d="M17.414 2.586a2 2 0 00-2.828 0L7 10.172V13h2.828l7.586-7.586a2 2 0 000-2.828z" />
            <path fill-rule="evenodd" d="M2 6a2 2 0 012-2h4a1 1 0 010 2H4v10h10v-4a1 1 0 112 0v4a2 2 0 01-2 2H4a2 2 0 01-2-2V6z" clip-rule="evenodd" />
          </svg>
        </button>
      </div>
      <div class="prose prose-sm max-w-none text-slate-600 leading-7 whitespace-pre-line">
        <p>{{ data?.full_synopsis || '暂无' }}</p>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import { useRoute } from 'vue-router'
import { NovelAPI } from '@/api/novel'

interface OverviewData {
  one_sentence_summary?: string | null
  target_audience?: string | null
  genre?: string | null
  style?: string | null
  tone?: string | null
  full_synopsis?: string | null
  cover_url?: string | null
}

const props = defineProps<{
  data: OverviewData | null
  editable?: boolean
}>()

const emit = defineEmits<{
  (e: 'edit', payload: { field: string; title: string; value: any }): void
  (e: 'coverUpdated', coverUrl: string): void
}>()

const route = useRoute()
const projectId = route.params.id as string

// Cover management state (admin only)
const coverUrl = ref<string | null>(props.data?.cover_url || null)
const isGenerating = ref(false)
const fileInputRef = ref<HTMLInputElement | null>(null)

// Watch for data changes to update cover URL
watch(() => props.data?.cover_url, (newCoverUrl) => {
  coverUrl.value = newCoverUrl || null
})

const coverImageSrc = computed(() => {
  const url = coverUrl.value
  if (!url) return ''
  if (url.startsWith('http') || url.startsWith('/')) return url
  return `/${url}`
})

const emitEdit = (field: string, title: string, value: any) => {
  if (!props.editable) return
  emit('edit', { field, title, value })
}

// Admin-only cover management methods
const handleGenerateCover = async () => {
  if (props.editable || !projectId || isGenerating.value) return
  
  isGenerating.value = true
  try {
    const result = await NovelAPI.generateCover(projectId)
    coverUrl.value = result.cover_url
    emit('coverUpdated', result.cover_url)
  } catch (error) {
    console.error('生成封面失败:', error)
    alert('生成封面失败，请重试')
  } finally {
    isGenerating.value = false
  }
}

const triggerFileUpload = () => {
  if (props.editable || isGenerating.value) return
  fileInputRef.value?.click()
}

const handleFileUpload = async (event: Event) => {
  if (props.editable || !projectId) return
  
  const target = event.target as HTMLInputElement
  if (!target.files || target.files.length === 0) return
  
  const file = target.files[0]
  
  // Validate file type
  if (!file.type.startsWith('image/')) {
    alert('请上传图片文件')
    return
  }
  
  // Validate file size (max 5MB)
  if (file.size > 5 * 1024 * 1024) {
    alert('图片文件不能超过 5MB')
    return
  }
  
  isGenerating.value = true
  try {
    const result = await NovelAPI.uploadCover(projectId, file)
    coverUrl.value = result.cover_url
    emit('coverUpdated', result.cover_url)
  } catch (error) {
    console.error('上传封面失败:', error)
    alert('上传封面失败，请重试')
  } finally {
    isGenerating.value = false
    target.value = '' // Reset input
  }
}

</script>

<script lang="ts">
import { defineComponent } from 'vue'

export default defineComponent({
  name: 'OverviewSection'
})
</script>
