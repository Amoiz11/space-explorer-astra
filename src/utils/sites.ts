import type { SunEarthSample } from '../types'

export const SITE_COLORS = ['#F472B6', '#2DD4BF', '#E8ECF4', '#818CF8', '#D6A77A']
export const siteColor = (i: number) => SITE_COLORS[i % SITE_COLORS.length]
export const siteLetter = (i: number) => String.fromCharCode(65 + (i % 26))

export function maxElevation(samples: SunEarthSample[], body: 'sun' | 'earth') {
  return samples.length ? Math.max(...samples.map((s) => s[body].el)) : null
}
