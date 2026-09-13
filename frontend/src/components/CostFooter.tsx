import { useEffect, useState } from 'react'
import { getTotalCost, onCostChange } from '../api'

export function CostFooter() {
  const [total, setTotal] = useState(getTotalCost)

  useEffect(() => onCostChange(setTotal), [])

  return (
    <footer className="cost-footer">
      Claude API利用料(このブラウザの累計): ${total.toFixed(4)}
    </footer>
  )
}
