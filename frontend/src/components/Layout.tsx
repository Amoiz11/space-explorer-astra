import { useEffect } from 'react'
import { Outlet, useLocation } from 'react-router-dom'
import { motion } from 'framer-motion'
import Nav from './Nav'
import Footer from './Footer'
import BackgroundScene from './BackgroundScene'
import ResearchDrawer from './ResearchDrawer'
import AssistantDrawer from './AssistantDrawer'

export default function Layout() {
  const { pathname } = useLocation()
  useEffect(() => { window.scrollTo(0, 0) }, [pathname])

  return (
    <div className="relative flex min-h-screen flex-col" style={{ background: 'var(--bg-0)' }}>
      {/* Fixed ambient background – z-index 0, behind everything */}
      <BackgroundScene />

      {/* Page content – z-index 1 */}
      <div className="relative z-10 flex flex-1 flex-col">
        <Nav />
        <motion.main
          key={pathname}
          initial={{ opacity: 0, y: 8 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.25 }}
          className="mx-auto w-full max-w-[1280px] px-4 pb-10 pt-4 md:px-6"
        >
          <Outlet />
        </motion.main>
        <Footer />
      </div>

      <AssistantDrawer />
      <ResearchDrawer />
    </div>
  )
}
