// Handsome Dan, Yale's bulldog, drawn in SVG (no image files), in his Yale-blue collar. Used as the cursor buddy,
// the chat avatar, and the home-page mascot.

export type DanMood = 'neutral' | 'smile' | 'lick'

type Props = {
  mood?: DanMood
  size?: number
  className?: string
  title?: string
}

const INK = '#2b1d14'
const FUR = '#f7f0e4'
const PATCH = '#d8a66b'
const MUZZLE = '#fffaf1'

export default function HandsomeDan({ mood = 'neutral', size = 64, className = '', title }: Props) {
  const happy = mood !== 'neutral'
  return (
    <svg
      viewBox="0 0 120 124"
      width={size}
      height={size}
      className={`dan dan-${mood} ${className}`}
      role={title ? 'img' : undefined}
      aria-label={title}
      aria-hidden={title ? undefined : true}
    >
      {/* Rose ears */}
      <path d="M22 40 C10 30 12 14 30 18 C38 20 40 30 36 38 Z" fill={PATCH} stroke={INK} strokeWidth="3" strokeLinejoin="round" />
      <path d="M98 40 C110 30 108 14 90 18 C82 20 80 30 84 38 Z" fill={PATCH} stroke={INK} strokeWidth="3" strokeLinejoin="round" />

      {/* Head */}
      <path
        d="M60 22 C88 22 106 38 106 62 C106 84 92 100 60 100 C28 100 14 84 14 62 C14 38 32 22 60 22 Z"
        fill={FUR}
        stroke={INK}
        strokeWidth="3"
      />
      {/* Tan patch over the left eye */}
      <path d="M28 44 C32 34 48 34 52 44 C55 52 48 62 38 61 C29 60 25 52 28 44 Z" fill={PATCH} opacity="0.85" />
      {/* Brow wrinkles */}
      <path d="M48 34 Q60 29 72 34" fill="none" stroke={INK} strokeWidth="2" strokeLinecap="round" opacity="0.55" />
      <path d="M52 40 Q60 37 68 40" fill="none" stroke={INK} strokeWidth="2" strokeLinecap="round" opacity="0.45" />

      {/* Eyes: round normally, happy arcs when smiling or licking */}
      {happy ? (
        <g fill="none" stroke={INK} strokeWidth="3.2" strokeLinecap="round">
          <path d="M37 56 Q43 50 49 56" />
          <path d="M71 56 Q77 50 83 56" />
        </g>
      ) : (
        <g className="dan-eyes">
          <circle cx="43" cy="55" r="5.5" fill={INK} />
          <circle cx="77" cy="55" r="5.5" fill={INK} />
          <circle cx="45" cy="53" r="1.8" fill="#fff" />
          <circle cx="79" cy="53" r="1.8" fill="#fff" />
        </g>
      )}

      {/* Muzzle and jowls */}
      <path d="M32 78 C32 64 46 62 60 62 C74 62 88 64 88 78 C88 92 76 98 60 98 C44 98 32 92 32 78 Z" fill={MUZZLE} stroke={INK} strokeWidth="2.5" />
      {/* Nose */}
      <path d="M50 66 C50 61 70 61 70 66 C70 72 64 75 60 75 C56 75 50 72 50 66 Z" fill={INK} />
      <ellipse cx="56" cy="65" rx="3" ry="1.5" fill="#fff" opacity="0.5" />
      {/* Philtrum + jowl lines */}
      <path d="M60 75 L60 80" stroke={INK} strokeWidth="2.5" strokeLinecap="round" />
      {mood === 'neutral' ? (
        <path d="M44 84 Q52 80 60 80 Q68 80 76 84" fill="none" stroke={INK} strokeWidth="2.5" strokeLinecap="round" />
      ) : (
        <path d="M40 80 Q50 92 60 82 Q70 92 80 80" fill="none" stroke={INK} strokeWidth="2.8" strokeLinecap="round" />
      )}

      {/* Underbite: lower jaw with two little teeth (the bulldog signature) */}
      {mood !== 'lick' && (
        <g>
          <path d="M46 86 Q60 96 74 86" fill="none" stroke={INK} strokeWidth="2.5" strokeLinecap="round" />
          <path d="M50 87 L52.5 81.5 L55 88 Z" fill="#fff" stroke={INK} strokeWidth="1.5" strokeLinejoin="round" />
          <path d="M65 88 L67.5 81.5 L70 87 Z" fill="#fff" stroke={INK} strokeWidth="1.5" strokeLinejoin="round" />
        </g>
      )}

      {/* Tongue for the lick */}
      {mood === 'lick' && (
        <g className="dan-tongue">
          <path d="M52 84 C52 96 56 104 61 104 C67 104 70 96 69 84 Z" fill="#e45c6e" stroke={INK} strokeWidth="2.2" strokeLinejoin="round" />
          <path d="M60.5 88 L60.5 99" stroke="#b83347" strokeWidth="1.8" strokeLinecap="round" />
        </g>
      )}

      {/* Cheek blush when happy */}
      {happy && (
        <g fill="#e45c6e" opacity="0.35">
          <ellipse cx="30" cy="72" rx="6" ry="3.5" />
          <ellipse cx="90" cy="72" rx="6" ry="3.5" />
        </g>
      )}

      {/* Yale-blue sweater collar with a white Y tag, like the real Handsome Dan's sweater */}
      <path d="M28 98 Q60 110 92 98 L92 106 Q60 118 28 106 Z" fill="#00356b" stroke={INK} strokeWidth="2.5" strokeLinejoin="round" />
      <path d="M34 103 Q60 113 86 103" fill="none" stroke="#fff" strokeWidth="1.4" opacity="0.8" />
      <circle cx="60" cy="114" r="8" fill="#fff" stroke={INK} strokeWidth="2.5" />
      <text x="60" y="118" textAnchor="middle" fontFamily="Graduate, serif" fontSize="11" fill="#00356b">
        Y
      </text>
    </svg>
  )
}
