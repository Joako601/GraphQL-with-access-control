import { useState, type FormEvent } from 'react'
import { CircleAlert, RefreshCw } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Card, CardContent } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { DEFAULT_PERIOD, validatePeriod, type Period } from '@/lib/period'

interface PeriodControlsProps {
  loading: boolean
  onSubmit: (period: Period) => void
}

const DATE_INPUT = 'h-10 rounded-full px-4 text-sm [color-scheme:dark]'

export function PeriodControls({ loading, onSubmit }: PeriodControlsProps) {
  const [period, setPeriod] = useState<Period>(DEFAULT_PERIOD)
  const [error, setError] = useState<string | null>(null)

  function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    const message = validatePeriod(period)
    setError(message)
    // Invalid ranges never reach the API.
    if (!message) onSubmit(period)
  }

  const update = (field: keyof Period) => (value: string) => setPeriod((p) => ({ ...p, [field]: value }))

  return (
    <Card className="rounded-2xl border border-white/[0.06] py-5 ring-0">
      <CardContent className="px-5">
        <form onSubmit={handleSubmit} className="flex flex-wrap items-end gap-4" aria-label="Controles de período">
          <div className="grid gap-2">
            <Label htmlFor="fromDate" className="text-muted-foreground">Desde</Label>
            <Input id="fromDate" type="date" value={period.fromDate} aria-invalid={!!error}
              onChange={(e) => update('fromDate')(e.target.value)} className={DATE_INPUT} />
          </div>
          <div className="grid gap-2">
            <Label htmlFor="toDate" className="text-muted-foreground">Hasta</Label>
            <Input id="toDate" type="date" value={period.toDate} aria-invalid={!!error}
              onChange={(e) => update('toDate')(e.target.value)} className={DATE_INPUT} />
          </div>
          <Button type="submit" disabled={loading} className="h-10 rounded-full bg-white px-5 text-black hover:bg-white/90">
            <RefreshCw className={loading ? 'animate-spin' : ''} />
            Actualizar
          </Button>
          {error && (
            <p role="alert" className="flex basis-full items-center gap-2 text-sm text-red-400">
              <CircleAlert className="size-4" />
              {error}
            </p>
          )}
        </form>
      </CardContent>
    </Card>
  )
}
