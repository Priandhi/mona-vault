// Reusable SRT/VTT parser for any React component that needs subtitle support.
// Drop-in: import { parseSubtitleFile } from './subtitle-parser' or copy verbatim.
//
// Tested with 4 input formats (verified 2026-06-13):
//   1. SRT full:  "00:00:01,000 --> 00:00:04,500\nHalo, apa kabar?"
//   2. VTT full:  "WEBVTT\n\n00:00:01.000 --> 00:00:04.500\nFirst line"
//   3. VTT short: "WEBVTT\n\n00:00.000 --> 00:02.000\nFirst line"
//   4. Long video:  "01:23:45,678 --> 01:23:50,000\n2.5 hours in" → 5025.68s start
//
// Returns: { cues: [{start, end, text}], type: 'srt'|'vtt', count: number }
// Cues are sorted by `start` ascending.

export function parseSubtitleFile(content, filename) {
  const isVTT = filename.toLowerCase().endsWith('.vtt') || content.trim().startsWith('WEBVTT')
  const cues = []
  const blocks = content
    .replace(/\r\n/g, '\n')
    .replace(/\r/g, '\n')
    .split(/\n\s*\n+/)

  const fullRe = /(\d{1,2}):(\d{2}):(\d{2})[.,](\d{1,3})\s*-->\s*(\d{1,2}):(\d{2}):(\d{2})[.,](\d{1,3})/
  const shortRe = /(\d{2}):(\d{2})[.,](\d{1,3})\s*-->\s*(\d{2}):(\d{2})[.,](\d{1,3})/

  for (const block of blocks) {
    const lines = block.split('\n').filter(l => l.trim())
    if (lines.length < 2) continue
    const timeLineIdx = lines.findIndex(l => l.includes('-->'))
    if (timeLineIdx === -1) continue
    const timeLine = lines[timeLineIdx]
    let start, end
    let m = timeLine.match(fullRe)
    if (m) {
      const toSec = (h, mn, s, ms) =>
        parseInt(h) * 3600 + parseInt(mn) * 60 + parseInt(s) + parseInt(ms.padEnd(3, '0')) / 1000
      start = toSec(m[1], m[2], m[3], m[4])
      end = toSec(m[5], m[6], m[7], m[8])
    } else {
      m = timeLine.match(shortRe)
      if (!m) continue
      const toSec = (mn, s, ms) =>
        parseInt(mn) * 60 + parseInt(s) + parseInt(ms.padEnd(3, '0')) / 1000
      start = toSec(m[1], m[2], m[3])
      end = toSec(m[4], m[5], m[6])
    }
    const text = lines.slice(timeLineIdx + 1).join('\n').trim()
    if (!text) continue
    cues.push({ start, end, text })
  }
  cues.sort((a, b) => a.start - b.start)
  return { cues, type: isVTT ? 'vtt' : 'srt', count: cues.length }
}

// Usage in a React component:
//   const handleSubtitleUpload = (e) => {
//     const file = e.target.files?.[0]
//     if (!file) return
//     if (file.size > 2 * 1024 * 1024) { setError('Max 2MB'); return }
//     const reader = new FileReader()
//     reader.onload = (evt) => {
//       const result = parseSubtitleFile(evt.target.result, file.name)
//       if (result.count === 0) { setError('No valid cues found'); return }
//       setSubtitleCues(result.cues)
//       setSubtitleName(file.name)
//     }
//     reader.readAsText(file)
//   }
