'use client'

import dynamic from 'next/dynamic'
import type { Institution } from './page'

const MapClient = dynamic(() => import('./MapClient'), {
  ssr: false,
  loading: () => (
    <div style={{ height: '100dvh', display: 'flex', alignItems: 'center', justifyContent: 'center', background: '#f9f9f9' }}>
      <p style={{ fontSize: 14, color: '#999', letterSpacing: '0.05em' }}>Loading map…</p>
    </div>
  ),
})

export default function MapWrapper({ institutions }: { institutions: Institution[] }) {
  return <MapClient institutions={institutions} />
}
