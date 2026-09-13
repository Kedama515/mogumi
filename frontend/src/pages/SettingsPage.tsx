export function SettingsPage({ onLogout }: { onLogout: () => void }) {
  return (
    <div className="page">
      <div className="card">
        <button className="ghost" onClick={onLogout}>
          ログアウト
        </button>
      </div>
    </div>
  )
}
