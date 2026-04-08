import { useCallback, useEffect, useState } from 'react'

type Theme = 'light' | 'dark'

function getSystemTheme(): Theme {
  return window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light'
}

function getStoredTheme(): Theme | null {
  const stored = localStorage.getItem('docling-theme')
  return stored === 'light' || stored === 'dark' ? stored : null
}

export function useTheme() {
  const [theme, setTheme] = useState<Theme>(() => getStoredTheme() ?? getSystemTheme())

  useEffect(() => {
    document.documentElement.setAttribute('data-theme', theme)
    localStorage.setItem('docling-theme', theme)
  }, [theme])

  useEffect(() => {
    const mql = window.matchMedia('(prefers-color-scheme: dark)')
    const handler = (e: MediaQueryListEvent) => {
      if (!getStoredTheme()) {
        setTheme(e.matches ? 'dark' : 'light')
      }
    }
    mql.addEventListener('change', handler)
    return () => mql.removeEventListener('change', handler)
  }, [])

  const toggleTheme = useCallback(() => {
    setTheme((prev) => (prev === 'dark' ? 'light' : 'dark'))
  }, [])

  return [theme, toggleTheme] as const
}
