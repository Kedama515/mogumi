import { useEffect, useState } from 'react'
import { api } from '../api'
import type { UserSettings } from '../types'

const APP_VERSION = '0.1.0'

const LIBRARIES = [
  { name: 'React', role: 'フロントエンドUI' },
  { name: 'Vite', role: 'フロントエンドビルドツール' },
  { name: 'TypeScript', role: 'フロントエンド言語' },
  { name: 'FastAPI', role: 'バックエンドAPIフレームワーク' },
  { name: 'SQLAlchemy', role: 'DB(ORM)' },
  { name: 'Anthropic Python SDK', role: '献立提案(Claude API)呼び出し' },
  { name: 'PyJWT / bcrypt', role: '認証' },
]

export function SettingsPage({
  onLogout,
  onBack,
}: {
  onLogout: () => void
  onBack: () => void
}) {
  const [settings, setSettings] = useState<UserSettings | null>(null)
  const [saveState, setSaveState] = useState<'idle' | 'saving' | 'saved' | 'error'>('idle')

  useEffect(() => {
    api.getSettings().then(setSettings)
  }, [])

  async function handleSave() {
    if (!settings) return
    setSaveState('saving')
    try {
      const updated = await api.updateSettings(settings)
      setSettings(updated)
      setSaveState('saved')
    } catch {
      setSaveState('error')
    }
  }

  return (
    <div className="page">
      <button className="ghost" onClick={onBack}>
        ← ホームへ戻る
      </button>

      <div className="card">
        <h3>個人設定</h3>
        <p className="muted">献立作成のたびに入力しなくていいように、普段使うデフォルト値をここで管理します。</p>
        {settings && (
          <>
            <div className="field-row">
              <label>
                人数
                <input
                  type="number"
                  min={1}
                  value={settings.default_servings}
                  onChange={(e) =>
                    setSettings({ ...settings, default_servings: Number(e.target.value) })
                  }
                />
              </label>
              <label>
                献立提案モード
                <select
                  value={settings.suggestion_mode}
                  onChange={(e) =>
                    setSettings({
                      ...settings,
                      suggestion_mode: e.target.value as 'batch' | 'confirm_menu',
                    })
                  }
                >
                  <option value="batch">一括サジェスト</option>
                  <option value="confirm_menu">メニューを確認してから</option>
                </select>
              </label>
            </div>

            <h4>被り回避の許容日数</h4>
            <p className="muted">数字が小さいほど厳しく被りを避けます。実際に使いながら調整してください。</p>
            <div className="field-row">
              <label>
                料理名(完全一致)
                <input
                  type="number"
                  min={0}
                  value={settings.avoid_days_dish_name}
                  onChange={(e) =>
                    setSettings({ ...settings, avoid_days_dish_name: Number(e.target.value) })
                  }
                />
              </label>
              <label>
                ジャンル(カレー/丼など)
                <input
                  type="number"
                  min={0}
                  value={settings.avoid_days_genre}
                  onChange={(e) =>
                    setSettings({ ...settings, avoid_days_genre: Number(e.target.value) })
                  }
                />
              </label>
            </div>
            <div className="field-row">
              <label>
                調理法・タンパク源
                <input
                  type="number"
                  min={0}
                  value={settings.avoid_days_method_protein}
                  onChange={(e) =>
                    setSettings({
                      ...settings,
                      avoid_days_method_protein: Number(e.target.value),
                    })
                  }
                />
              </label>
              <label>
                和洋中
                <input
                  type="number"
                  min={0}
                  value={settings.avoid_days_cuisine}
                  onChange={(e) =>
                    setSettings({ ...settings, avoid_days_cuisine: Number(e.target.value) })
                  }
                />
              </label>
            </div>
          </>
        )}
        <button onClick={handleSave} disabled={!settings || saveState === 'saving'}>
          {saveState === 'saved' ? '保存しました' : saveState === 'saving' ? '保存中…' : '保存する'}
        </button>
        {saveState === 'error' && <p className="error">保存に失敗しました</p>}
      </div>

      <div className="card">
        <h3>バージョン情報</h3>
        <p className="muted">mogumi v{APP_VERSION}</p>

        <h4>主要ライブラリ</h4>
        <ul className="library-list">
          {LIBRARIES.map((lib) => (
            <li key={lib.name}>
              <strong>{lib.name}</strong> <span className="muted">— {lib.role}</span>
            </li>
          ))}
        </ul>
      </div>

      <div className="card">
        <h3>アカウント</h3>
        <button className="ghost" onClick={onLogout}>
          ログアウト
        </button>
      </div>
    </div>
  )
}
