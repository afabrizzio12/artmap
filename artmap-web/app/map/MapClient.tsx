'use client'

import { useEffect, useRef, useState } from 'react'
import maplibregl from 'maplibre-gl'
import { layers, labels, namedTheme } from 'protomaps-themes-base'
import type { StyleSpecification } from 'maplibre-gl'
import SidePanel from './SidePanel'
import type { Institution } from './page'
import Link from 'next/link'

const PARIS: [number, number] = [2.3522, 48.8566]
const NAVY = '#1B2A4A'

function buildProtomapsStyle(apiKey: string): StyleSpecification {
  return {
    version: 8,
    glyphs: 'https://protomaps.github.io/basemaps-assets/fonts/{fontstack}/{range}.pbf',
    sprite: 'https://protomaps.github.io/basemaps-assets/sprites/v4/light',
    sources: {
      protomaps: {
        type: 'vector',
        tiles: [`https://api.protomaps.com/tiles/v4/{z}/{x}/{y}.mvt?key=${apiKey}`],
        maxzoom: 15,
        attribution:
          '© <a href="https://protomaps.com">Protomaps</a> © <a href="https://openstreetmap.org">OpenStreetMap</a>',
      },
    },
    layers: [
      ...layers('protomaps', namedTheme('light')),
      ...labels('protomaps', 'light', 'en'),
    ],
  }
}

function institutionsToGeoJSON(insts: Institution[]): GeoJSON.FeatureCollection {
  return {
    type: 'FeatureCollection',
    features: insts.map((inst) => ({
      type: 'Feature',
      geometry: { type: 'Point', coordinates: [inst.lng, inst.lat] },
      properties: {
        id: inst.id,
        name: inst.name,
        city: inst.city,
        country: inst.country,
        artwork_count: inst.artwork_count,
        website: inst.website,
      },
    })),
  }
}

export default function MapClient({ institutions }: { institutions: Institution[] }) {
  const containerRef = useRef<HTMLDivElement>(null)
  const mapRef = useRef<maplibregl.Map | null>(null)
  const [selected, setSelected] = useState<Institution | null>(null)

  useEffect(() => {
    // Guard: don't double-init (React Strict Mode runs effects twice in dev)
    if (mapRef.current) return
    const container = containerRef.current
    if (!container) return

    const apiKey = process.env.NEXT_PUBLIC_PROTOMAPS_KEY ?? ''
    const style = apiKey
      ? buildProtomapsStyle(apiKey)
      : 'https://tiles.openfreemap.org/styles/liberty'

    const map = new maplibregl.Map({
      container,
      style,
      center: PARIS,
      zoom: 11,
      attributionControl: false,
    })

    mapRef.current = map

    map.addControl(new maplibregl.AttributionControl({ compact: true }), 'bottom-left')
    map.addControl(new maplibregl.NavigationControl({ showCompass: false }), 'bottom-right')

    map.on('load', () => {
      map.addSource('institutions', {
        type: 'geojson',
        data: institutionsToGeoJSON(institutions),
        cluster: true,
        clusterMaxZoom: 12,
        clusterRadius: 48,
      })

      // Cluster circles — scale with count
      map.addLayer({
        id: 'clusters',
        type: 'circle',
        source: 'institutions',
        filter: ['has', 'point_count'],
        paint: {
          'circle-color': NAVY,
          'circle-radius': ['step', ['get', 'point_count'], 18, 10, 24, 50, 32],
          'circle-stroke-width': 2,
          'circle-stroke-color': '#ffffff',
          'circle-opacity': 0.88,
        },
      })

      // Cluster count label
      map.addLayer({
        id: 'cluster-count',
        type: 'symbol',
        source: 'institutions',
        filter: ['has', 'point_count'],
        layout: {
          'text-field': '{point_count_abbreviated}',
          'text-size': 12,
          'text-font': ['Noto Sans Regular'],
        },
        paint: { 'text-color': '#ffffff' },
      })

      // Individual pin
      map.addLayer({
        id: 'unclustered-point',
        type: 'circle',
        source: 'institutions',
        filter: ['!', ['has', 'point_count']],
        paint: {
          'circle-color': NAVY,
          'circle-radius': 8,
          'circle-stroke-width': 2.5,
          'circle-stroke-color': '#ffffff',
          'circle-opacity': 0.9,
        },
      })

      // Click cluster → zoom in
      map.on('click', 'clusters', async (e) => {
        const [feature] = map.queryRenderedFeatures(e.point, { layers: ['clusters'] })
        if (!feature) return
        const source = map.getSource('institutions') as maplibregl.GeoJSONSource
        try {
          const zoom = await source.getClusterExpansionZoom(feature.properties.cluster_id)
          map.easeTo({
            center: (feature.geometry as GeoJSON.Point).coordinates as [number, number],
            zoom: zoom + 0.5,
            duration: 400,
          })
        } catch { /* ignore */ }
      })

      // Click pin → side panel
      map.on('click', 'unclustered-point', (e) => {
        const feature = e.features?.[0]
        if (!feature) return
        const p = feature.properties!
        const [lng, lat] = (feature.geometry as GeoJSON.Point).coordinates
        setSelected({
          id: p.id, name: p.name, city: p.city, country: p.country,
          lat, lng, artwork_count: p.artwork_count, website: p.website,
        })
        map.easeTo({ center: [lng, lat], offset: [0, 40], duration: 300 })
      })

      // Click empty space → close panel
      map.on('click', (e) => {
        const hits = map.queryRenderedFeatures(e.point, {
          layers: ['unclustered-point', 'clusters'],
        })
        if (hits.length === 0) setSelected(null)
      })

      // Pointer cursor on interactive layers
      for (const layer of ['clusters', 'unclustered-point']) {
        map.on('mouseenter', layer, () => { map.getCanvas().style.cursor = 'pointer' })
        map.on('mouseleave', layer, () => { map.getCanvas().style.cursor = '' })
      }
    })

    return () => {
      map.remove()
      mapRef.current = null
    }
  }, [institutions])

  return (
    <div style={{ position: 'relative', width: '100%', height: '100dvh', overflow: 'hidden' }}>
      {/* Map canvas — explicit px sizing so MapLibre always gets a non-zero box */}
      <div ref={containerRef} style={{ position: 'absolute', inset: 0 }} />

      {/* Back nav */}
      <div style={{ position: 'absolute', top: 16, left: 16, zIndex: 10 }}>
        <Link
          href="/"
          className="flex items-center gap-2 h-9 px-4 bg-white/95 backdrop-blur-sm border border-zinc-200/80 rounded-full shadow-sm text-sm font-medium text-[#111111] hover:bg-white transition-colors"
        >
          <svg width="14" height="14" viewBox="0 0 14 14" fill="none">
            <path d="M9 2L4 7l5 5" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"/>
          </svg>
          ArtMap
        </Link>
      </div>

      {selected && (
        <SidePanel institution={selected} onClose={() => setSelected(null)} />
      )}
    </div>
  )
}
