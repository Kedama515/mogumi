import { useEffect, useState } from 'react'
import './App.css'
import { clearToken, getToken, setUnauthorizedHandler } from './api'
import { CostFooter } from './components/CostFooter'
import { FridgePage } from './pages/FridgePage'
import { HistoryPage } from './pages/HistoryPage'
import { LoginPage } from './pages/LoginPage'
import { PantryPage } from './pages/PantryPage'
import { RecipePage } from './pages/RecipePage'
import { SuggestPage } from './pages/SuggestPage'

const TABS = [
  { key: 'suggest', label: '献立提案', Component: SuggestPage },
  { key: 'fridge', label: '冷蔵庫', Component: FridgePage },
  { key: 'pantry', label: '常備品', Component: PantryPage },
  { key: 'recipes', label: 'レシピ', Component: RecipePage },
  { key: 'history', label: '履歴', Component: HistoryPage },
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
        <div className="header-row">
          <h1>mogumi</h1>
          <button className="ghost" onClick={handleLogout}>
            ログアウト
          </button>
        </div>
        <nav className="tabs">
          {TABS.map((t) => (
            <button
              key={t.key}
              className={t.key === tab ? 'tab active' : 'tab'}
              onClick={() => setTab(t.key)}
            >
              {t.label}
            </button>
          ))}
        </nav>
      </header>
      <main>
        <Active />
      </main>
      <CostFooter />
    </div>
  )
}

export default App
