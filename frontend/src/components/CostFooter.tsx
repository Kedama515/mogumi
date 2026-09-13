import { useEffect, useState } from 'react'
import { getTotalCost, onCostChange } from '../api'

export function CostFooter() {
  const [total, setTotal] = useState(getTotalCost)
  const [last, setLast] = useState<number | null>(null)

  useEffect(
    () =>
      onCostChange((update) => {
        setLast(update.last)
        setTotal(update.total)
      }),
    [],
  )

  return (
    <footer className="cost-footer">
      Claude API利用料 {last != null && <>今回: ${last.toFixed(4)} / </>}
      累計(このブラウザ): ${total.toFixed(4)}
    </footer>
  )
}
