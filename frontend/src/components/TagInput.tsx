import { useState } from 'react'

export function TagInput({
  value,
  onChange,
  placeholder,
}: {
  value: string[]
  onChange: (tags: string[]) => void
  placeholder?: string
}) {
  const [draft, setDraft] = useState('')

  function commitDraft() {
    const trimmed = draft.trim()
    if (trimmed) {
      onChange([...value, trimmed])
    }
    setDraft('')
  }

  function handleKeyDown(e: React.KeyboardEvent<HTMLInputElement>) {
    if (e.key === ' ' || e.key === 'Enter') {
      e.preventDefault()
      commitDraft()
    } else if (e.key === 'Backspace' && draft === '' && value.length > 0) {
      onChange(value.slice(0, -1))
    }
  }

  function removeTag(index: number) {
    onChange(value.filter((_, i) => i !== index))
  }

  return (
    <div className="tag-input">
      {value.map((tag, i) => (
        <span key={i} className="tag-chip">
          {tag}
          <button type="button" onClick={() => removeTag(i)} aria-label={`${tag}を削除`}>
            ×
          </button>
        </span>
      ))}
      <input
        value={draft}
        onChange={(e) => setDraft(e.target.value)}
        onKeyDown={handleKeyDown}
        onBlur={commitDraft}
        placeholder={value.length === 0 ? placeholder : ''}
      />
    </div>
  )
}
