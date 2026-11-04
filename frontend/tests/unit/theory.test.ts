import { describe, expect, it } from 'vitest'
import type { TheoryArticle } from '../../app/types'
import { contentSummary, fileSizeText, isHttpUrl, uploadErrorText } from '../../app/utils/theory'
import { ApiError } from '../../app/utils/api'

const base: TheoryArticle = {
  id: '1',
  title: 'Bài',
  mainCat: 'doc-hieu',
  subCat: 'doc-hieu-tho',
  type: 'reference',
  format: 'mixed',
  icon: '📚',
  desc: '',
  content: '',
}

describe('knowledge post helpers', () => {
  it('accepts only http(s) links', () => {
    expect(isHttpUrl('https://example.com/a?b=1')).toBe(true)
    expect(isHttpUrl('http://example.com')).toBe(true)
    expect(isHttpUrl('javascript:alert(1)')).toBe(false)
    expect(isHttpUrl('ftp://example.com')).toBe(false)
    expect(isHttpUrl('example.com')).toBe(false)
  })
  it('formats file sizes', () => {
    expect(fileSizeText(512)).toBe('512 B')
    expect(fileSizeText(2048)).toBe('2 KB')
    expect(fileSizeText(10 * 1024 * 1024)).toBe('10 MB')
  })
  it('summarises a combined post', () => {
    const article: TheoryArticle = {
      ...base,
      content: '<p>Bài</p>',
      attachments: [
        { id: 'a', kind: 'image', name: 'a.png' },
        { id: 'b', kind: 'image', name: 'b.png' },
        { id: 'c', kind: 'link', name: 'Link', url: 'https://x.y' },
        { id: 'd', kind: 'file', name: 'd.pdf' },
      ],
    }
    expect(contentSummary(article)).toBe('📝 Bài viết · 🖼️ 2 ảnh · 🔗 1 liên kết · 📎 1 tệp')
  })
  it('counts legacy single-format posts', () => {
    expect(contentSummary({ ...base, format: 'image', fileData: 'data:image/png;base64,AA' })).toBe(
      '🖼️ 1 ảnh',
    )
    expect(
      contentSummary({ ...base, format: 'pdf', fileData: 'data:application/pdf;base64,AA' }),
    ).toBe('📎 1 tệp')
    expect(contentSummary(base)).toBe('')
  })
})

describe('upload error messages', () => {
  it('explains rejected files in Vietnamese', () => {
    expect(uploadErrorText(new ApiError('x', 415))).toMatch(/Định dạng không hỗ trợ/)
    expect(uploadErrorText(new ApiError('x', 413))).toMatch(/10 MB/)
    expect(uploadErrorText(new ApiError('x', 409))).toMatch(/20/)
    expect(uploadErrorText(new Error('Mất mạng'))).toBe('Mất mạng')
  })
})
