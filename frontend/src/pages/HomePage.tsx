export function HomePage({ onOpenSettings }: { onOpenSettings: () => void }) {
  return (
    <div className="page">
      <div className="home-header">
        <h2>ホーム</h2>
        <button className="icon-button" onClick={onOpenSettings} aria-label="設定">
          ⚙️
        </button>
      </div>
      <div className="card">
        <p className="muted">
          下のタブから、冷蔵庫・レシピ・献立作成・カレンダーにアクセスできます。
        </p>
      </div>
    </div>
  )
}
