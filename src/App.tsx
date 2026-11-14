import { Route, Routes } from 'react-router-dom'
import Layout from './components/Layout'
import HomePage from './features/home/HomePage'
import LunarPage from './features/lunar/LunarPage'
import LunarComparePage from './features/lunar/LunarComparePage'
import MissionsPage from './features/missions/MissionsPage'
import MissionProfile from './features/missions/MissionProfile'
import MapPage from './features/map/MapPage'
import GalleryPage from './features/gallery/GalleryPage'
import TimeMachinePage from './features/timemachine/TimeMachinePage'
import ComparePage from './features/compare/ComparePage'
import AssistantPage from './features/assistant/AssistantPage'
import AdminPage from './features/admin/AdminPage'

export default function App() {
  return (
    <Routes>
      <Route element={<Layout />}>
        <Route path="/" element={<HomePage />} />
        <Route path="/missions" element={<MissionsPage />} />
        <Route path="/missions/:missionId" element={<MissionProfile />} />
        <Route path="/explorers/:id/map" element={<MapPage />} />
        <Route path="/explorers/:id/gallery" element={<GalleryPage />} />
        <Route path="/time-machine" element={<TimeMachinePage />} />
        <Route path="/compare" element={<ComparePage />} />
        <Route path="/lunar" element={<LunarPage />} />
        <Route path="/lunar/compare" element={<LunarComparePage />} />
        <Route path="/assistant" element={<AssistantPage />} />
        <Route path="/admin" element={<AdminPage />} />
      </Route>
    </Routes>
  )
}
