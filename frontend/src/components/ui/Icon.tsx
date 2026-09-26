import type { SVGProps } from 'react'

const paths = {
  grid: <><rect x="3.5" y="3.5" width="7" height="7" rx="1.5" /><rect x="13.5" y="3.5" width="7" height="7" rx="1.5" /><rect x="3.5" y="13.5" width="7" height="7" rx="1.5" /><rect x="13.5" y="13.5" width="7" height="7" rx="1.5" /></>,
  chart: <><path d="M4 19.5h16" /><path d="M6.5 16V10m5 6V5m5 11v-4" /><path d="m5.5 7.5 5-3 5 5 3-2" /></>,
  calendar: <><rect x="3.5" y="5" width="17" height="16" rx="2" /><path d="M7.5 3v4m8-4v4M4 9.5h16" /><path d="M8 13h.01M12 13h.01M16 13h.01M8 17h.01M12 17h.01" /></>,
  book: <><path d="M5 4.5A2.5 2.5 0 0 1 7.5 2H20v17H7.5A2.5 2.5 0 0 0 5 21.5z" /><path d="M5 4.5v17m3-15h8m-8 4h8" /></>,
  pencil: <><path d="m4 16.5-.8 4.3 4.3-.8L20 7.5 16.5 4z" /><path d="m14.5 6 3.5 3.5" /></>,
  check: <><path d="M12 3a9 9 0 1 0 9 9" /><path d="m8 12 2.5 2.5L21 4" /></>,
  file: <><path d="M6 3.5h8l4 4v13H6z" /><path d="M14 3.5v5h5m-9 4h5m-5 4h5" /></>,
  spark: <><path d="m12 3 1.7 5.3L19 10l-5.3 1.7L12 17l-1.7-5.3L5 10l5.3-1.7z" /><path d="m19 16 .8 2.2L22 19l-2.2.8L19 22l-.8-2.2L16 19l2.2-.8z" /></>,
  users: <><path d="M16 20v-1.5a4 4 0 0 0-4-4H7a4 4 0 0 0-4 4V20" /><circle cx="9.5" cy="7" r="3.5" /><path d="M17 4a3.5 3.5 0 0 1 0 6.8m4 9.2v-1.5a4 4 0 0 0-3-3.9" /></>,
  menu: <><path d="M4 6h16M4 12h16M4 18h16" /></>,
  close: <><path d="m6 6 12 12M18 6 6 18" /></>,
  arrow: <><path d="M5 12h14m-6-6 6 6-6 6" /></>,
  plus: <><path d="M12 5v14M5 12h14" /></>,
  logout: <><path d="M10 17l5-5-5-5m5 5H3" /><path d="M12 3h6a2 2 0 0 1 2 2v14a2 2 0 0 1-2 2h-6" /></>,
  chevron: <path d="m9 18 6-6-6-6" />,
} as const

export type IconName = keyof typeof paths

export function Icon({ name, ...props }: SVGProps<SVGSVGElement> & { name: IconName }) {
  return (
    <svg
      aria-hidden="true"
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="1.7"
      strokeLinecap="round"
      strokeLinejoin="round"
      {...props}
    >
      {paths[name]}
    </svg>
  )
}
