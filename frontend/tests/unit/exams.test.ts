import { describe, expect, it } from 'vitest'
import { duration, newQuestions, totalScore, gradeTotal, clockText } from '../../app/utils/exams'
import { readDatabase, saveTable } from '../../app/utils/storage'
import type { Exam, ExamType, Result } from '../../app/types'

describe('exam rules retained from the HTML app', () => {
  it.each<[ExamType, string, number, number, number]>([
    ['practice', 'doc-hieu', 5, 4, 1500],
    ['practice', 'viet-doan', 1, 2, 2100],
    ['practice', 'viet-bai', 1, 5, 3600],
    ['mock', 'vao-10', 7, 10, 7200],
    ['mock', 'hsg', 7, 10, 7200],
  ])('%s / %s preserves question count, points and time', (type, group, count, points, seconds) => {
    const exam: Exam = {
      id: 'one',
      title: 'Đề',
      targetGroup: group,
      passage: '',
      questions: newQuestions(type, group),
    }
    expect(exam.questions).toHaveLength(count)
    expect(totalScore(exam)).toBe(points)
    expect(duration(type, group)).toBe(seconds)
  })
  it('rejects invalid scores and sums valid marks', () => {
    const exam: Exam = {
      id: 'one',
      title: 'Đề',
      targetGroup: 'viet-doan',
      passage: '',
      questions: newQuestions('practice', 'viet-doan'),
    }
    const result = {
      answers: { q0: { ans: 'Bài làm', teacherScore: 2, selfScore: 1.75 } },
    } as unknown as Result
    expect(gradeTotal(result, exam, 'teacherScore')).toBe(2)
    expect(gradeTotal(result, exam, 'selfScore')).toBe(1.75)
    for (const invalid of [-0.25, 2.25, NaN]) {
      result.answers.q0!.teacherScore = invalid
      expect(() => gradeTotal(result, exam, 'teacherScore')).toThrow()
    }
  })
  it('formats overtime without wrapping at an hour', () => {
    expect(clockText(7200)).toBe('120:00')
    expect(clockText(-61)).toBe('-01:01')
  })
})

describe('legacy browser storage', () => {
  function storage() {
    const records = new Map<string, string>()
    return {
      getItem: (key: string) => records.get(key) ?? null,
      setItem: (key: string, value: string) => records.set(key, value),
    } as Storage
  }
  it('reads and preserves legacy IDs and related records', () => {
    const s = storage()
    s.setItem(
      'vu_users',
      JSON.stringify([
        {
          id: 'old-student',
          classId: 'old-class',
          role: 'student',
          password: 'test',
          fullName: 'Học sinh',
        },
      ]),
    )
    s.setItem('vu_classes', JSON.stringify([{ id: 'old-class', name: '9A' }]))
    const db = readDatabase(s)
    expect(db.users[0]?.classId).toBe(db.classes[0]?.id)
    saveTable(s, 'classes', db.classes)
    expect(readDatabase(s).classes).toEqual(db.classes)
    expect(db.assignments).toEqual([])
  })
  it('does not overwrite malformed legacy data', () => {
    const s = storage()
    s.setItem('vu_results', 'broken JSON')
    expect(() => readDatabase(s)).toThrow()
    expect(s.getItem('vu_results')).toBe('broken JSON')
  })
})
