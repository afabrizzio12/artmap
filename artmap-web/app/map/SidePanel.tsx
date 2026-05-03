'use client'

import { useEffect } from 'react'
import type { Institution } from './page'

interface Props {
  institution: Institution
  onClose: () => void
}

export default function SidePanel({ institution, onClose }: Props) {
  useEffect(() => {
    const handler = (e: KeyboardEvent) => {
      if (e.key === 'Escape') onClose()
    }
    window.addEventListener('keydown', handler)
    return () => window.removeEventListener('keydown', handler)
  }, [onClose])

  const location = [institution.city, institution.country].filter(Boolean).join(', ')

  return (
    <>
      {/* Mobile backdrop */}
      <div
        className="fixed inset-0 z-20 bg-black/20 sm:hidden"
        onClick={onClose}
      />

      {/* Panel */}
      <div
        className="
          fixed z-30 bg-white
          /* mobile: slide up from bottom */
          bottom-0 left-0 right-0 rounded-t-2xl shadow-2xl
          animate-slide-up
          /* desktop: slide in from right */
          sm:bottom-auto sm:left-auto sm:top-0 sm:right-0
          sm:h-full sm:w-96 sm:rounded-none sm:shadow-[-4px_0_24px_rgba(0,0,0,0.08)]
          sm:animate-slide-right
          flex flex-col
        "
      >
        {/* Header */}
        <div className="flex items-start justify-between px-6 pt-6 pb-5 border-b border-zinc-100">
          <div className="flex-1 min-w-0 pr-4">
            {location && (
              <p className="text-[10px] font-semibold text-zinc-400 uppercase tracking-[0.12em] mb-1.5">
                {location}
              </p>
            )}
            <h2 className="text-xl font-semibold text-[#111111] leading-snug">
              {institution.name}
            </h2>
          </div>
          <button
            onClick={onClose}
            className="flex-shrink-0 w-8 h-8 flex items-center justify-center rounded-full text-zinc-400 hover:text-zinc-700 hover:bg-zinc-100 transition-colors"
            aria-label="Close panel"
          >
            <svg width="14" height="14" viewBox="0 0 14 14" fill="none">
              <path d="M1 1l12 12M13 1L1 13" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" />
            </svg>
          </button>
        </div>

        {/* Artwork count */}
        <div className="px-6 py-5 border-b border-zinc-100">
          <p className="text-[10px] font-semibold text-zinc-400 uppercase tracking-[0.12em] mb-2">
            Collection
          </p>
          <p className="text-4xl font-semibold text-[#1B2A4A] tabular-nums leading-none">
            {institution.artwork_count.toLocaleString()}
          </p>
          <p className="text-sm text-zinc-400 mt-2">artworks indexed</p>
        </div>

        {/* Actions */}
        <div className="px-6 py-5 flex flex-col gap-3">
          {institution.website && (
            <a
              href={institution.website}
              target="_blank"
              rel="noopener noreferrer"
              className="inline-flex items-center gap-1.5 text-sm font-medium text-[#1B2A4A] hover:opacity-70 transition-opacity"
            >
              Visit website
              <svg width="12" height="12" viewBox="0 0 12 12" fill="none">
                <path d="M2 10L10 2M10 2H4M10 2v6" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" />
              </svg>
            </a>
          )}
        </div>

        {/* Mobile drag handle */}
        <div className="absolute top-2.5 left-1/2 -translate-x-1/2 w-10 h-1 bg-zinc-200 rounded-full sm:hidden" />
      </div>
    </>
  )
}
