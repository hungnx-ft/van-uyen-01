import type { TheoryArticle } from '../types'
import { ApiError } from './api'

/** Mirrors the backend limits for knowledge post attachments. */
export const MAX_ATTACHMENTS = 20
export const MAX_FILE_BYTES = 10 * 1024 * 1024
export const ACCEPTED_FILE_TYPES = [
  'image/png',
  'image/jpeg',
  'image/gif',
  'image/webp',
  'image/avif',
  'application/pdf',
  '.docx',
  'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
].join(',')

export function isHttpUrl(value: string) {
  try {
    const url = new URL(value)
    return url.protocol === 'https:' || url.protocol === 'http:'
  } catch {
    return false
  }
}

export function fileSizeText(bytes: number) {
  if (bytes < 1024) return `${bytes} B`
  if (bytes < 1024 * 1024) return `${Math.round(bytes / 1024)} KB`
  return `${Math.round((bytes / 1024 / 1024) * 10) / 10} MB`
}

/** Icons for what a post contains, shown on its card. */
export function contentSummary(article: TheoryArticle) {
  const attachments = article.attachments || []
  const count = (kind: string) => attachments.filter((item) => item.kind === kind).length
  const legacy = article.fileData ? article.format : ''
  const parts: string[] = []
  if (article.content?.trim()) parts.push('📝 Bài viết')
  const images = count('image') + (legacy === 'image' ? 1 : 0)
  const links = count('link') + (legacy === 'link' ? 1 : 0)
  const files = count('file') + (legacy === 'pdf' ? 1 : 0)
  if (images) parts.push(`🖼️ ${images} ảnh`)
  if (links) parts.push(`🔗 ${links} liên kết`)
  if (files) parts.push(`📎 ${files} tệp`)
  return parts.join(' · ')
}

/** A Vietnamese reason for a failed attachment upload. */
export function uploadErrorText(error: unknown) {
  const status = error instanceof ApiError ? error.status : 0
  if (status === 415) return 'Định dạng không hỗ trợ (chỉ nhận ảnh, PDF, DOCX).'
  if (status === 413) return `Tệp quá lớn (tối đa ${fileSizeText(MAX_FILE_BYTES)}).`
  if (status === 409) return `Bài đã đủ ${MAX_ATTACHMENTS} tệp/liên kết.`
  if (status === 422) return 'Tệp rỗng hoặc không hợp lệ.'
  return (error as Error)?.message || 'Không tải lên được.'
}
