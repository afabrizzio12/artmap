import { supabase } from '@/lib/supabase'
import MapWrapper from './MapWrapper'

export type Institution = {
  id: string
  name: string
  city: string | null
  country: string | null
  lat: number
  lng: number
  website: string | null
  artwork_count: number
}

async function getInstitutions(): Promise<Institution[]> {
  const { data, error } = await supabase
    .from('institutions')
    .select('id, name, city, country, lat, lng, website, artworks(count)')
    .not('lat', 'is', null)
    .not('lng', 'is', null)

  if (error || !data) return []

  return data.map((inst) => ({
    id: inst.id,
    name: inst.name,
    city: inst.city,
    country: inst.country,
    lat: inst.lat as number,
    lng: inst.lng as number,
    website: inst.website,
    artwork_count:
      Array.isArray(inst.artworks) && inst.artworks.length > 0
        ? (inst.artworks[0] as { count: number }).count ?? 0
        : 0,
  }))
}

export default async function MapPage() {
  const institutions = await getInstitutions()
  return <MapWrapper institutions={institutions} />
}
