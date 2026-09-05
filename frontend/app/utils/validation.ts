import type { Database } from '../types'

type Row = Record<string, unknown>

function fail(path: string): never {
  throw new Error(`Dữ liệu ${path} không hợp lệ. Dữ liệu gốc được giữ nguyên.`)
}
function object(value: unknown, path: string): Row {
  if (!value || typeof value !== 'object' || Array.isArray(value)) fail(path)
  return value as Row
}
function text(value: unknown, path: string, fallback?: string): string {
  if (value === undefined && fallback !== undefined) return fallback
  if (typeof value !== 'string') fail(path)
  return value
}
function id(value: unknown, path: string): string {
  const result = text(value, path)
  if (!result.trim()) fail(path)
  return result
}
function number(value: unknown, path: string, fallback?: number): number {
  if (value === undefined && fallback !== undefined) return fallback
  if (typeof value !== 'number' || !Number.isFinite(value) || value < 0) fail(path)
  return value
}
function choice(value: unknown, values: string[], path: string, fallback?: string): string {
  const result = text(value, path, fallback)
  if (!values.includes(result)) fail(path)
  return result
}
function optionalFields(row: Row, path: string) {
  for (const key of ['classId', 'className', 'schoolName', 'genre', 'fileData', 'teacherComment']) {
    if (row[key] !== undefined) text(row[key], `${path}.${key}`)
  }
  if (row.isClassStudent !== undefined && typeof row.isClassStudent !== 'boolean') {
    fail(`${path}.isClassStudent`)
  }
}
function exam(value: unknown, path: string): Row {
  const row = object(value, path)
  if (!Array.isArray(row.questions) || !row.questions.length) fail(`${path}.questions`)
  optionalFields(row, path)
  return {
    ...row,
    id: id(row.id, `${path}.id`),
    title: text(row.title, `${path}.title`),
    targetGroup: text(row.targetGroup, `${path}.targetGroup`),
    passage: text(row.passage, `${path}.passage`, ''),
    questions: row.questions.map((value, i) => {
      const p = `${path}.questions[${i}]`,
        q = object(value, p)
      return {
        ...q,
        q: text(q.q, `${p}.q`, ''),
        a: text(q.a, `${p}.a`, ''),
        score: number(q.score, `${p}.score`),
      }
    }),
  }
}

/** Validate runtime data as well as TypeScript callers; fill only safe legacy defaults. */
export function normalizeTable<K extends keyof Database>(table: K, value: unknown): Database[K] {
  if (!Array.isArray(value)) fail(table)
  const ids = new Set<string>()
  const rows = value.map((value, index) => {
    const path = `${table}[${index}]`,
      row = object(value, path)
    const rowId = id(row.id, `${path}.id`)
    if (ids.has(rowId)) fail(`${path}.id (trùng ID ${rowId})`)
    ids.add(rowId)
    optionalFields(row, path)
    switch (table) {
      case 'users':
        return {
          ...row,
          id: rowId,
          role: choice(row.role, ['teacher', 'student'], `${path}.role`),
          password: text(row.password, `${path}.password`),
          fullName: text(row.fullName, `${path}.fullName`, rowId),
        }
      case 'classes':
        return {
          ...row,
          id: rowId,
          name: text(row.name, `${path}.name`),
          year: text(row.year, `${path}.year`, ''),
        }
      case 'theory_articles':
        return {
          ...row,
          id: rowId,
          title: text(row.title, `${path}.title`),
          mainCat: text(row.mainCat, `${path}.mainCat`),
          subCat: text(row.subCat, `${path}.subCat`),
          type: choice(row.type, ['core', 'reference', 'sharing'], `${path}.type`, 'reference'),
          format: choice(row.format, ['text', 'image', 'pdf', 'link'], `${path}.format`, 'text'),
          icon: text(row.icon, `${path}.icon`, '📚'),
          desc: text(row.desc, `${path}.desc`, ''),
          content: text(row.content, `${path}.content`, ''),
        }
      case 'practice_exams':
      case 'mock_exams':
        return exam(row, path)
      case 'assignments':
        return {
          ...row,
          id: rowId,
          examId: id(row.examId, `${path}.examId`),
          examType: choice(row.examType, ['practice', 'mock'], `${path}.examType`),
          classId: id(row.classId, `${path}.classId`),
          createdAt: number(row.createdAt, `${path}.createdAt`),
          examTitle: text(row.examTitle, `${path}.examTitle`),
        }
      case 'results': {
        const answers = object(row.answers, `${path}.answers`)
        if (
          row.attempt !== undefined &&
          (!Number.isInteger(row.attempt) || number(row.attempt, `${path}.attempt`) < 1)
        )
          fail(`${path}.attempt`)
        for (const key of ['selfScore', 'teacherScore'])
          if (row[key] !== undefined) number(row[key], `${path}.${key}`)
        return {
          ...row,
          id: rowId,
          studentId: id(row.studentId, `${path}.studentId`),
          studentName: text(row.studentName, `${path}.studentName`, String(row.studentId)),
          examId: id(row.examId, `${path}.examId`),
          examTitle: text(row.examTitle, `${path}.examTitle`),
          examType: choice(row.examType, ['practice', 'mock'], `${path}.examType`),
          status: choice(row.status, ['pending', 'graded'], `${path}.status`),
          maxScore: number(row.maxScore, `${path}.maxScore`),
          timeSpent: number(row.timeSpent, `${path}.timeSpent`, 0),
          submittedAt: number(row.submittedAt, `${path}.submittedAt`),
          ...(row.examSnapshot === undefined
            ? {}
            : { examSnapshot: exam(row.examSnapshot, `${path}.examSnapshot`) }),
          answers: Object.fromEntries(
            Object.entries(answers).map(([key, value]) => {
              if (!/^q\d+$/.test(key)) fail(`${path}.answers.${key}`)
              const p = `${path}.answers.${key}`,
                a = object(value, p)
              optionalFields(a, p)
              return [
                key,
                {
                  ...a,
                  ans: text(a.ans, `${p}.ans`, ''),
                  selfScore: number(a.selfScore, `${p}.selfScore`, 0),
                  teacherScore: number(a.teacherScore, `${p}.teacherScore`, 0),
                },
              ]
            }),
          ),
        }
      }
    }
  })
  // Detach nested objects so later edits to a form cannot silently change stored state.
  return JSON.parse(JSON.stringify(rows)) as Database[K]
}
