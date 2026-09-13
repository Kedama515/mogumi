import { useState } from 'react'
import './App.css'
import { FridgePage } from './pages/FridgePage'
import { HistoryPage } from './pages/HistoryPage'
import { PantryPage } from './pages/PantryPage'
import { SuggestPage } from './pages/SuggestPage'

const TABS = [
  { key: 'suggest', label: '献立提案', Component: SuggestPage },
  { key: 'fridge', label: '冷蔵庫', Component: FridgePage },
  { key: 'pantry', label: '常備品', Component: PantryPage },
  { key: 'history', label: '履歴', Component: HistoryPage },
] as const

function App() {
  const [tab, setTab] = useState<(typeof TABS)[number]['key']>('suggest')
  const Active = TABS.find((t) => t.key === tab)!.Component

  return (
    <div className="app">
      <header className="app-header">
        <h1>mogumi</h1>
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
    </div>
  )
}

export default App
