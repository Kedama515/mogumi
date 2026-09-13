import { useEffect, useState } from 'react'
import './App.css'
import { clearToken, getToken, setUnauthorizedHandler } from './api'
import { CostFooter } from './components/CostFooter'
import { FridgeManagementPage } from './pages/FridgeManagementPage'
import { HistoryPage } from './pages/HistoryPage'
import { LoginPage } from './pages/LoginPage'
import { RecipePage } from './pages/RecipePage'
import { SettingsPage } from './pages/SettingsPage'
import { SuggestPage } from './pages/SuggestPage'

const TABS = [
  { key: 'suggest', label: '献立作成', Component: SuggestPage },
  { key: 'fridge', label: '冷蔵庫', Component: FridgeManagementPage },
  { key: 'recipes', label: 'レシピ', Component: RecipePage },
  { key: 'history', label: '履歴', Component: HistoryPage },
  { key: 'settings', label: '設定', Component: null },
] as const

function App() {
  const [tab, setTab] = useState<(typeof TABS)[number]['key']>('suggest')
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

  const Active = TABS.find((t) => t.key === tab)!.Component

  return (
    <div className="app">
      <header className="app-header">
        <h1>mogumi</h1>
      </header>
      <main>{Active ? <Active /> : <SettingsPage onLogout={handleLogout} />}</main>
      <CostFooter />
      <nav className="bottom-nav">
        {TABS.map((t) => (
          <button
            key={t.key}
            className={t.key === tab ? 'bottom-nav-item active' : 'bottom-nav-item'}
            onClick={() => setTab(t.key)}
          >
            {t.label}
          </button>
        ))}
      </nav>
    </div>
  )
}

export default App
