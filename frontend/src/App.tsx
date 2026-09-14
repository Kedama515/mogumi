import { useEffect, useState } from 'react'
import './App.css'
import { clearToken, getToken, setUnauthorizedHandler } from './api'
import { CostFooter } from './components/CostFooter'
import { FridgeManagementPage } from './pages/FridgeManagementPage'
import { HistoryPage } from './pages/HistoryPage'
import { HomePage } from './pages/HomePage'
import { LoginPage } from './pages/LoginPage'
import { RecipePage } from './pages/RecipePage'
import { SettingsPage } from './pages/SettingsPage'
import { SuggestPage } from './pages/SuggestPage'

const TABS = [
  { key: 'fridge', label: '冷蔵庫', icon: '🧊', Component: FridgeManagementPage, main: false },
  { key: 'recipes', label: 'レシピ', icon: '📖', Component: RecipePage, main: false },
  { key: 'suggest', label: '献立', icon: '🍽️', Component: SuggestPage, main: true },
  { key: 'history', label: 'カレンダー', icon: '📅', Component: HistoryPage, main: false },
  { key: 'home', label: 'ホーム', icon: '🏠', Component: null, main: false },
] as const

type TabKey = (typeof TABS)[number]['key'] | 'settings'

function App() {
  const [tab, setTab] = useState<TabKey>('suggest')
  const [authed, setAuthed] = useState(() => Boolean(getToken()))

  useEffect(() => {
    setUnauthorizedHandler(() => setAuthed(false))
  }, [])

  if (!authed) {
    return <LoginPage onLogin={() => setAuthed(true)} />
  }

  function handleLogout() {
    clearToken()
    setAuthed(false)
  }

  function renderMain() {
    if (tab === 'settings') {
      return <SettingsPage onLogout={handleLogout} onBack={() => setTab('home')} />
    }
    if (tab === 'home') {
      return <HomePage onOpenSettings={() => setTab('settings')} />
    }
    const def = TABS.find((t) => t.key === tab)!
    const Comp = def.Component!
    return <Comp />
  }

  return (
    <div className="app">
      <header className="app-header">
        <h1>mogumi</h1>
      </header>
      <main>{renderMain()}</main>
      <CostFooter />
      <nav className="bottom-nav">
        {TABS.map((t) => {
          const isActive = tab === t.key || (t.key === 'home' && tab === 'settings')
          if (t.main) {
            return (
              <button
                key={t.key}
                className={isActive ? 'bottom-nav-item main active' : 'bottom-nav-item main'}
                onClick={() => setTab(t.key)}
              >
                <span className="main-circle">{t.icon}</span>
                <span className="nav-label">{t.label}</span>
              </button>
            )
          }
          return (
            <button
              key={t.key}
              className={isActive ? 'bottom-nav-item active' : 'bottom-nav-item'}
              onClick={() => setTab(t.key)}
            >
              <span className="icon">{t.icon}</span>
              <span className="nav-label">{t.label}</span>
            </button>
          )
        })}
      </nav>
    </div>
  )
}

export default App
