import { useEffect, useRef, useState } from 'react'
import HandsomeDan, { type DanMood } from './HandsomeDan'

const STORAGE_KEY = 'cc-dan-cursor'
const OFFSET = { x: 22, y: 20 } // sit beside the pointer, never on top of what you're clicking
const IDLE_SPIN_MS = 6000
const BARKS = ['Woof!', 'Boola Boola!', 'Beat Harvard!']

// Only on real mice, and not for people who've asked their OS for less motion.
function canRun(): boolean {
  return (
    window.matchMedia('(pointer: fine)').matches && !window.matchMedia('(prefers-reduced-motion: reduce)').matches
  )
}

export function useDanCursorSetting(): [boolean, (on: boolean) => void] {
  const [on, setOn] = useState(() => localStorage.getItem(STORAGE_KEY) !== 'off')
  useEffect(() => {
    const sync = () => setOn(localStorage.getItem(STORAGE_KEY) !== 'off')
    window.addEventListener('cc-dan-setting', sync)
    return () => window.removeEventListener('cc-dan-setting', sync)
  }, [])
  return [
    on,
    (next) => {
      localStorage.setItem(STORAGE_KEY, next ? 'on' : 'off')
      window.dispatchEvent(new Event('cc-dan-setting'))
    },
  ]
}

export default function DanCursor() {
  const [enabled] = useDanCursorSetting()
  const [supported] = useState(canRun)
  const [mood, setMood] = useState<DanMood>('neutral')
  const [spinning, setSpinning] = useState(false)
  const [woof, setWoof] = useState<string | null>(null)
  const wrapRef = useRef<HTMLDivElement>(null)
  const clicks = useRef(0)

  useEffect(() => {
    if (!enabled || !supported) return
    const el = wrapRef.current!
    const target = { x: -100, y: -100 }
    const pos = { x: -100, y: -100 }
    let facing = 1
    let visible = false
    let frame = 0
    let idleTimer = 0
    let moodTimer = 0

    // Position updates go straight to the DOM each frame; React only re-renders on mood changes.
    const tick = () => {
      const dx = target.x - pos.x
      const dy = target.y - pos.y
      pos.x += dx * 0.2
      pos.y += dy * 0.2
      if (Math.abs(dx) > 2) facing = dx > 0 ? 1 : -1
      const tilt = Math.max(-18, Math.min(18, dx * 0.35))
      el.style.transform = `translate3d(${pos.x + OFFSET.x}px, ${pos.y + OFFSET.y}px, 0) rotate(${tilt}deg) scaleX(${facing})`
      frame = requestAnimationFrame(tick)
    }

    const resetIdle = () => {
      window.clearTimeout(idleTimer)
      idleTimer = window.setTimeout(() => {
        setSpinning(true)
        window.setTimeout(() => setSpinning(false), 900)
        resetIdle()
      }, IDLE_SPIN_MS)
    }

    const onMove = (e: PointerEvent) => {
      target.x = e.clientX
      target.y = e.clientY
      if (!visible) {
        visible = true
        pos.x = e.clientX
        pos.y = e.clientY
        el.classList.add('visible')
      }
      resetIdle()
    }
    const onLeave = () => {
      visible = false
      el.classList.remove('visible')
    }
    const onDown = (e: PointerEvent) => {
      clicks.current += 1
      setMood(clicks.current % 2 ? 'lick' : 'smile')
      if (clicks.current % 5 === 0) {
        setWoof(BARKS[(clicks.current / 5 - 1) % BARKS.length])
        window.setTimeout(() => setWoof(null), 1100)
      }
      window.clearTimeout(moodTimer)
      moodTimer = window.setTimeout(() => setMood('neutral'), 650)
      burstHearts(e.clientX, e.clientY)
      resetIdle()
    }

    frame = requestAnimationFrame(tick)
    window.addEventListener('pointermove', onMove)
    window.addEventListener('pointerdown', onDown)
    document.documentElement.addEventListener('pointerleave', onLeave)
    resetIdle()
    return () => {
      cancelAnimationFrame(frame)
      window.clearTimeout(idleTimer)
      window.clearTimeout(moodTimer)
      window.removeEventListener('pointermove', onMove)
      window.removeEventListener('pointerdown', onDown)
      document.documentElement.removeEventListener('pointerleave', onLeave)
    }
  }, [enabled, supported])

  if (!enabled || !supported) return null
  return (
    <div ref={wrapRef} className="dan-cursor" aria-hidden="true">
      <div className={`dan-cursor-body ${spinning ? 'spin' : ''} ${mood !== 'neutral' ? 'bounce' : ''}`}>
        <HandsomeDan mood={mood} size={58} />
      </div>
      {woof && <span className="dan-woof">{woof}</span>}
    </div>
  )
}

// Little hearts and paw prints that pop out where you click.
function burstHearts(x: number, y: number) {
  const symbols = ['♥', '♥', '🐾']
  for (let i = 0; i < 5; i++) {
    const el = document.createElement('span')
    el.className = 'dan-heart'
    el.textContent = symbols[i % symbols.length]
    const angle = (-90 + (i - 2) * 28) * (Math.PI / 180)
    el.style.left = `${x}px`
    el.style.top = `${y}px`
    el.style.setProperty('--dx', `${Math.cos(angle) * (34 + Math.random() * 18)}px`)
    el.style.setProperty('--dy', `${Math.sin(angle) * (34 + Math.random() * 18)}px`)
    document.body.appendChild(el)
    window.setTimeout(() => el.remove(), 800)
  }
}
