import React, { useState } from 'react'
import { Lock, Eye } from 'lucide-react'

/**
 * Password-based age gate for ICLIX 21+ section.
 * Two-step: warning → password form. localStorage remembers "verified".
 *
 * Usage:
 *   <AdultRoute>
 *     {verified ? <AdultHome /> : <AgeGate onVerified={...} />}
 *   </AdultRoute>
 *
 * To change the password, update AGE_PASSWORD below. Clue shows below input.
 */

const AGE_KEY = 'iclix_21_verified'
const AGE_PASSWORD = 'jokowi'  // ← change this
const AGE_CLUE = 'presiden indonesia ke 7'  // ← user-facing hint, keep small

export default function AgeGate({ onVerified }) {
  const [step, setStep] = useState(0) // 0: warning, 1: password
  const [pw, setPw] = useState('')
  const [showPw, setShowPw] = useState(false)
  const [shake, setShake] = useState(false)
  const [err, setErr] = useState('')

  const submitPw = (e) => {
    e?.preventDefault()
    if (pw.trim().toLowerCase() === AGE_PASSWORD) {
      localStorage.setItem(AGE_KEY, '1')
      onVerified?.()
    } else {
      setErr('Password salah, coba lagi.')
      setShake(true)
      setTimeout(() => { setShake(false); setErr('') }, 800)
      setPw('')
    }
  }

  if (step === 0) {
    return (
      <div className="adult-agegate">
        <div className="agegate-bg">
          <div className="agegate-glow agegate-glow-1" />
          <div className="agegate-glow agegate-glow-2" />
        </div>
        <div className="agegate-box">
          <div className="agegate-icon">
            <Lock size={48} color="#e50914" />
          </div>
          <h1 className="agegate-title">21+ CONTENT</h1>
          <div className="agegate-subtitle">ICLIX 21+</div>
          <p className="agegate-warning">
            Bagian ini cuma buat orang yang udah <b>21 tahun ke atas</b>. Konten di sini mengandung materi eksplisit yang mungkin gak cocok buat semua orang.
          </p>
          <p className="agegate-disclaimer">
            Dengan melanjutkan, lo nyatain bahwa lo sudah berusia minimal 21 tahun dan setuju mengakses konten dewasa sesuai hukum yang berlaku di wilayah lo. Semua aktivitas didokumentasikan untuk kepatuhan hukum.
          </p>
          <div className="agegate-buttons">
            <button className="agegate-btn agegate-btn-no" onClick={() => window.history.back()}>
              ✕ Keluar
            </button>
            <button className="agegate-btn agegate-btn-yes" onClick={() => setStep(1)}>
              Saya 21+ → Lanjut
            </button>
          </div>
        </div>
      </div>
    )
  }

  return (
    <div className="adult-agegate">
      <div className="agegate-bg">
        <div className="agegate-glow agegate-glow-1" />
        <div className="agegate-glow agegate-glow-2" />
      </div>
      <div className={`agegate-box agegate-box-confirm ${shake ? 'shake' : ''}`}>
        <h2 className="agegate-confirm-title">Verifikasi Usia</h2>
        <p className="agegate-confirm-sub">Masukkan password untuk lanjut</p>
        <form onSubmit={submitPw} className="agegate-pw-form">
          <div className="agegate-pw-wrap">
            <input
              autoFocus
              type={showPw ? 'text' : 'password'}
              className="agegate-input"
              placeholder="Password..."
              value={pw}
              onChange={e => setPw(e.target.value)}
            />
            <button
              type="button"
              className="agegate-pw-toggle"
              onClick={() => setShowPw(s => !s)}
              tabIndex={-1}
              aria-label={showPw ? 'Sembunyikan' : 'Tampilkan'}
            >
              {showPw ? '🙈' : '👁'}
            </button>
          </div>
          <button type="submit" className="agegate-btn agegate-btn-yes agegate-pw-submit">
            Masuk →
          </button>
        </form>
        {err && <div className="agegate-pw-err">{err}</div>}
        <div className="agegate-pw-clue">{AGE_CLUE}</div>
        <button
          className="agegate-btn-back"
          onClick={() => { setStep(0); setPw(''); setErr('') }}
        >
          ← Kembali
        </button>
      </div>
    </div>
  )
}

// Hook for parent components to check verification
export function useAgeVerified() {
  const [verified, setVerified] = useState(() =>
    typeof window !== 'undefined' && localStorage.getItem(AGE_KEY) === '1'
  )
  return { verified, setVerified, reset: () => {
    localStorage.removeItem(AGE_KEY)
    setVerified(false)
  }}
}
