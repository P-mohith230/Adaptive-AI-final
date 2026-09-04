import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import {
  History,
  Lock,
  Search,
  User,
} from 'lucide-react'

import { reconciliation } from '@/lib/api'
import { Card, CardContent } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Input } from '@/components/ui/input'
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table'
import type { ReconciliationAuditLog } from '@/types/reconciliation'

export default function AuditTrailPage() {
  const [searchTerm, setSearchTerm] = useState('')

  const { data: logs, isLoading } = useQuery<ReconciliationAuditLog[]>({
    queryKey: ['reconciliation-audit-logs'],
    queryFn: () => reconciliation.getAuditLog(100),
    refetchInterval: 10000,
  })

  const filteredLogs = (logs || []).filter((l) => {
    if (!searchTerm.trim()) return true
    const term = searchTerm.toLowerCase()
    return (
      l.action.toLowerCase().includes(term) ||
      l.actor.toLowerCase().includes(term) ||
      l.decision.toLowerCase().includes(term) ||
      l.reason.toLowerCase().includes(term)
    )
  })

  const getActorBadge = (actor: string) => {
    if (actor.startsWith('user:')) {
      return (
        <Badge className="bg-primary/10 text-primary border-primary/20 flex items-center gap-1 font-mono text-[10px]">
          <User className="h-3 w-3" />
          {actor.replace('user:', '')}
        </Badge>
      )
    }
    if (actor.includes('ai_controller')) {
      return (
        <Badge className="bg-sky-500/10 text-sky-500 border-sky-500/20 font-mono text-[10px]">
          AI Controller v1
        </Badge>
      )
    }
    return (
      <Badge variant="outline" className="font-mono text-[10px]">
        Deterministic Engine
      </Badge>
    )
  }

  const getActionBadge = (action: string) => {
    if (action.includes('approval')) {
      return <Badge className="bg-emerald-500/15 text-emerald-600 border-emerald-500/30">APPROVED</Badge>
    }
    if (action.includes('rejection')) {
      return <Badge variant="destructive">REJECTED</Badge>
    }
    if (action.includes('investigation')) {
      return <Badge className="bg-sky-500/15 text-sky-600 border-sky-500/30">INVESTIGATED</Badge>
    }
    return <Badge variant="outline">{action}</Badge>
  }

  return (
    <div className="flex-1 space-y-6 p-6">
      {/* Header */}
      <div className="flex flex-col gap-4 md:flex-row md:items-center md:justify-between border-b pb-6">
        <div>
          <div className="flex items-center gap-2">
            <Badge variant="outline" className="bg-primary/10 text-primary border-primary/30">
              Financial Compliance
            </Badge>
            <Badge variant="secondary" className="font-mono text-xs flex items-center gap-1">
              <Lock className="h-3 w-3 text-emerald-500" />
              Append-Only Ledger
            </Badge>
          </div>
          <h1 className="text-2xl font-bold tracking-tight mt-1 text-foreground">Immutable Audit Trail</h1>
          <p className="text-muted-foreground text-sm">
            Every autonomous reconciliation and human decision is immutably logged with actor provenance, confidence scores, and timestamps.
          </p>
        </div>
      </div>

      {/* Search Bar */}
      <div className="flex items-center justify-between gap-4">
        <div className="relative w-80">
          <Search className="absolute left-3 top-2.5 h-4 w-4 text-muted-foreground" />
          <Input
            placeholder="Search action, actor, decision, reason..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="pl-9"
          />
        </div>
      </div>

      {/* Audit Log Table */}
      <Card>
        <CardContent className="p-0">
          {isLoading ? (
            <div className="py-16 text-center text-muted-foreground">Loading audit records...</div>
          ) : filteredLogs.length === 0 ? (
            <div className="py-16 text-center">
              <History className="h-10 w-10 text-muted-foreground/50 mx-auto mb-2" />
              <p className="font-medium text-foreground">No audit entries found</p>
              <p className="text-sm text-muted-foreground">Run reconciliation or review an exception to generate audit logs.</p>
            </div>
          ) : (
            <div className="overflow-x-auto">
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead className="w-[170px]">Timestamp (UTC)</TableHead>
                    <TableHead className="w-[150px]">Actor</TableHead>
                    <TableHead className="w-[130px]">Action</TableHead>
                    <TableHead className="w-[140px]">Decision</TableHead>
                    <TableHead className="min-w-[240px]">Rationale / Evidence</TableHead>
                    <TableHead className="w-[180px]">State Transition</TableHead>
                    <TableHead className="w-[90px] text-right">Version</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {filteredLogs.map((log) => (
                    <TableRow key={log.id}>
                      <TableCell className="font-mono text-xs text-muted-foreground whitespace-nowrap">
                        {new Date(log.created_at).toLocaleString()}
                      </TableCell>
                      <TableCell>{getActorBadge(log.actor)}</TableCell>
                      <TableCell>{getActionBadge(log.action)}</TableCell>
                      <TableCell className="font-mono text-xs font-semibold text-foreground">{log.decision}</TableCell>
                      <TableCell className="text-xs text-foreground/90 leading-relaxed">
                        {log.reason}
                      </TableCell>
                      <TableCell className="font-mono text-[11px] text-muted-foreground whitespace-nowrap">
                        {log.previous_state && log.new_state ? (
                          <span>
                            {log.previous_state} → <span className="font-bold text-foreground">{log.new_state}</span>
                          </span>
                        ) : (
                          '—'
                        )}
                      </TableCell>
                      <TableCell className="text-right font-mono text-[10px] text-muted-foreground">{log.agent_version}</TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  )
}
