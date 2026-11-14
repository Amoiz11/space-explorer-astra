import { getSunEarth, getWindows } from '../../services'
import type { Analysis } from '../../store/lunar'
import type { SiteResult } from '../../types'
import { useAsync } from '../../utils/useAsync'

export function useLunarData(analysis: Analysis | null) {
  return useAsync<SiteResult[] | null>(async () => {
    if (!analysis) return null
    return Promise.all(
      analysis.siteIds.map(async (siteId) => {
        const [sunEarth, windows] = await Promise.all([
          getSunEarth(siteId, analysis.start, analysis.end),
          getWindows(siteId, analysis.start, analysis.end),
        ])
        return { siteId, sunEarth, windows }
      }),
    )
  }, [analysis?.nonce])
}
