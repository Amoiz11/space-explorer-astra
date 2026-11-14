import { bodiesMock, datasetsMock, importsMock } from '../mocks/home'
import { makeCompare, makeSolar, makeSunEarth, makeTerrain, makeWindows, sitesMock } from '../mocks/lunar'
import {
  answerFor, compareMetrics, imagesFor, missionsMock, positionsFor, profileFor, sourceFor,
} from '../mocks/missions'
import type {
  AssistantAnswer, Body, CompareMetric, CompareResult, Dataset, ExplorerImage, ExplorerPosition, ImportRow,
  Mission, MissionProfileData, Site, SolarEstimate, SolarInputs, SourceInfo, SunEarth, Terrain, Windows,
} from '../types'
import { respond } from './mockClient'

const sites: Site[] = [...sitesMock]

export const getBodies = () => respond<Body[]>(bodiesMock)
export const getDatasets = () => respond<Dataset[]>(datasetsMock)
export const getImports = () => respond<ImportRow[]>(importsMock)

export const getMissions = (bodyId: 'mars' | 'moon') => respond<Mission[]>(missionsMock.filter((m) => m.body === bodyId))
export const getAllMissions = () => respond<Mission[]>(missionsMock)
export const getMission = (missionId: string) => respond<MissionProfileData | null>(profileFor(missionId))
export const getExplorerLocations = (explorerId: string) => respond<ExplorerPosition[]>(positionsFor(explorerId))
export const getExplorerImages = (explorerId: string) => respond<ExplorerImage[]>(imagesFor(explorerId))
export const compareMissions = (missionIds: string[]) => respond<CompareMetric[]>(compareMetrics(missionIds))
export const askAssistant = (question: string) => respond<AssistantAnswer>(answerFor(question))
export const getSource = (productId: string) => respond<SourceInfo>(sourceFor(productId))

export const getSites = () => respond<Site[]>([...sites])

export async function createSite(site: Omit<Site, 'id'>) {
  const created: Site = { ...site, id: `site-${String(Date.now()).slice(-6)}` }
  const saved = await respond<Site>(created)
  sites.push(saved)
  return saved
}
export async function updateSite(site: Site) {
  const saved = await respond<Site>(site)
  const i = sites.findIndex((s) => s.id === saved.id)
  if (i >= 0) sites[i] = saved
  return saved
}
export async function deleteSite(id: string) {
  await respond(true)
  const i = sites.findIndex((s) => s.id === id)
  if (i >= 0) sites.splice(i, 1)
  return true
}

export const getSunEarth = (siteId: string, start: string, end: string) =>
  respond<SunEarth>(makeSunEarth(siteId, start, end))
export const getWindows = (siteId: string, start: string, end: string) =>
  respond<Windows>(makeWindows(siteId, start, end))
export const getTerrain = (siteId: string) => respond<Terrain>(makeTerrain(siteId))
export const estimateSolar = (siteId: string, inputs: SolarInputs) => respond<SolarEstimate>(makeSolar(siteId, inputs))
export const compareSites = (siteIds: string[], dates: string[]) => respond<CompareResult>(makeCompare(siteIds, dates))
