import Link from 'next/link'
import { supabase } from '@/lib/supabase'

async function getCounts() {
  const [artworks, artists, institutions] = await Promise.all([
    supabase.from('artworks').select('*', { count: 'exact', head: true }),
    supabase.from('artists').select('*', { count: 'exact', head: true }),
    supabase.from('institutions').select('*', { count: 'exact', head: true }),
  ])
  return {
    artworks: artworks.count ?? 0,
    artists: artists.count ?? 0,
    institutions: institutions.count ?? 0,
  }
}

export default async function Home() {
  const counts = await getCounts()

  const stats = [
    { label: 'Artworks', value: counts.artworks },
    { label: 'Artists', value: counts.artists },
    { label: 'Institutions', value: counts.institutions },
  ]

  return (
    <main className="min-h-screen bg-zinc-50 flex flex-col items-center justify-center px-6">
      <div className="max-w-2xl w-full space-y-10">
        <div>
          <h1 className="text-4xl font-bold tracking-tight text-zinc-900">ArtMap</h1>
          <p className="mt-2 text-zinc-500 text-lg">A global map of artworks, artists, and institutions.</p>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
          {stats.map(({ label, value }) => (
            <div key={label} className="bg-white rounded-2xl border border-zinc-200 p-6 shadow-sm">
              <p className="text-sm font-medium text-zinc-500 uppercase tracking-wide">{label}</p>
              <p className="mt-2 text-3xl font-semibold text-zinc-900">
                {value.toLocaleString()}
              </p>
            </div>
          ))}
        </div>

        <Link
          href="/map"
          className="inline-flex items-center gap-2 h-11 px-6 rounded-full bg-[#1B2A4A] text-white text-sm font-medium hover:bg-[#253a66] transition-colors"
        >
          Explore the map →
        </Link>
      </div>
    </main>
  )
}
