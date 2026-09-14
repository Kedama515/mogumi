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
  return (
    <div className="page">
      <button className="ghost" onClick={onBack}>
        ← ホームへ戻る
      </button>

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
        <button className="ghost" onClick={onLogout}>
          ログアウト
        </button>
      </div>
    </div>
  )
}
