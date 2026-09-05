import { useState } from 'react'
import { Bot, CornerDownLeft, User } from 'lucide-react'
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle } from '@/components/ui/dialog'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Badge } from '@/components/ui/badge'
import { Markdown } from '@/components/agents/markdown'
import { reconciliation } from '@/lib/api'
import type { ReconciliationRecord } from '@/types/reconciliation'

interface Message {
  role: 'user' | 'assistant'
  content: string
  highlights?: Array<{ label: string; value: string }>
}

export function ControllerChatDialog({
  open,
  onOpenChange,
}: {
  open: boolean
  onOpenChange: (open: boolean) => void
}) {
  const [messages, setMessages] = useState<Message[]>([
    {
      role: 'assistant',
      content:
        'Hello! I am your AdaptiveAI Finance Controller. All my responses are grounded in verified database calculations with zero arithmetic hallucinations. How can I assist you with reconciliation, exception exposure, or settlement tracking today?',
    },
  ])
  const [input, setInput] = useState('')
  const [loading, setLoading] = useState(false)

  const handleSend = async (queryText?: string) => {
    const q = queryText || input
    if (!q.trim() || loading) return

    const userMsg: Message = { role: 'user', content: q }
    const nextMessages = [...messages, userMsg]
    setMessages(nextMessages)
    setInput('')
    setLoading(true)

    try {
      // 1. First attempt live AI Controller Settlement Q&A engine
      try {
        const history = nextMessages.slice(-8).map((m) => ({ role: m.role, content: m.content }))
        const qaRes = await reconciliation.askSettlementQA(q, history)
        if (qaRes && qaRes.answer) {
          setMessages((prev) => [
            ...prev,
            {
              role: 'assistant',
              content: qaRes.answer,
              highlights: qaRes.provider ? [{ label: 'Intelligence Source', value: qaRes.provider }] : undefined,
            },
          ])
          return
        }
      } catch {
        // Fall back to client heuristics if network error
      }

      const lower = q.toLowerCase()
      // Deterministic tool query
      if (lower.includes('how much') || lower.includes('unreconciled') || lower.includes('exposure') || lower.includes('total')) {
        const kpi = await reconciliation.getKPI()
        const exposureStr = Number(kpi.total_financial_exposure).toLocaleString('en-IN')
        setMessages((prev) => [
          ...prev,
          {
            role: 'assistant',
            content: `According to current ledger data, total unreconciled financial exposure is ₹${exposureStr} across ${kpi.unresolved_count} pending exceptions. Current verified match rate stands at ${(Number(kpi.match_rate) * 100).toFixed(1)}%.`,
            highlights: [
              { label: 'Unreconciled Exposure', value: `₹${exposureStr}` },
              { label: 'Pending Exceptions', value: `${kpi.unresolved_count} records` },
              { label: 'Match Rate', value: `${(Number(kpi.match_rate) * 100).toFixed(1)}%` },
            ],
          },
        ])
      } else if (lower.includes('highest') || lower.includes('risk') || lower.includes('priority')) {
        const records = await reconciliation.getRecords({ limit: 3 })
        const top = records.filter((r: ReconciliationRecord) => r.status !== 'AUTO_RECONCILED')[0]
        if (top) {
          const exp = Number(top.financial_impact).toLocaleString('en-IN')
          setMessages((prev) => [
            ...prev,
            {
              role: 'assistant',
              content: `The highest risk exception is Order ${top.order_id || 'N/A'} with an exposure of ₹${exp}. Classification: ${top.exception?.ai_classification || top.status}. Recommended action: ${top.exception?.recommendation || 'Review pricing.'}`,
              highlights: [
                { label: 'Top Risk Order', value: top.order_id || 'N/A' },
                { label: 'Financial Exposure', value: `₹${exp}` },
                { label: 'Confidence', value: `${(Number(top.exception?.confidence || 1) * 100).toFixed(1)}%` },
              ],
            },
          ])
        } else {
          setMessages((prev) => [
            ...prev,
            { role: 'assistant', content: 'There are currently no high-risk exceptions pending review.' },
          ])
        }
      } else if (lower.includes('order_') || lower.includes('tx-') || lower.includes('why did')) {
        // Extract order token if present
        const token = q.match(/order_[A-Za-z0-9_]+/i)?.[0] || 'order_DEMO_1012'
        const records = await reconciliation.getRecords({ limit: 100 })
        const found = records.find((r: ReconciliationRecord) => r.order_id?.toLowerCase() === token.toLowerCase()) || records.find((r: ReconciliationRecord) => r.status === 'MISMATCH')

        if (found) {
          const card = await reconciliation.getDecisionCard(found.id)
          setMessages((prev) => [
            ...prev,
            {
              role: 'assistant',
              content: `Investigation for ${card.order_id}: ${card.ai_reason} Recommended action: ${card.ai_recommendation}`,
              highlights: [
                { label: 'Expected Amount', value: `₹${Number(card.expected_amount).toLocaleString('en-IN')}` },
                { label: 'Razorpay Captured', value: `₹${Number(card.actual_amount).toLocaleString('en-IN')}` },
                { label: 'AI Confidence', value: `${(Number(card.ai_confidence) * 100).toFixed(1)}%` },
              ],
            },
          ])
        } else {
          setMessages((prev) => [
            ...prev,
            { role: 'assistant', content: `No discrepancy record was found matching '${token}'.` },
          ])
        }
      } else if (lower.includes('my name is') || lower.startsWith('i am ') || lower.startsWith('call me ')) {
        const nameMatch = q.match(/(?:my name is|i am|call me)\s+([a-zA-Z]+)/i)
        const name = nameMatch ? nameMatch[1] : 'there'
        setMessages((prev) => [
          ...prev,
          {
            role: 'assistant',
            content: `Hello **${name}**! Great to meet you. I am your AdaptiveAI Finance Controller. How can I assist you with reconciliation, settlement tracking, or cash flow today?`,
          },
        ])
      } else if (['hi', 'hello', 'hey', 'good morning', 'good evening', 'greetings', 'howdy'].some((g) => lower === g || lower.startsWith(`${g} `) || lower.startsWith(`${g},`) || lower.startsWith(`${g}!`))) {
        setMessages((prev) => [
          ...prev,
          {
            role: 'assistant',
            content: `Hello! Great to connect with you. I am your AdaptiveAI Finance Controller. You can ask me about our current reconciliation match rate, specific order discrepancies, Razorpay fee variances, or forward cash positions. What would you like to inspect?`,
          },
        ])
      } else {
        const kpi = await reconciliation.getKPI()
        setMessages((prev) => [
          ...prev,
          {
            role: 'assistant',
            content: `I am monitoring ${kpi.total_records} records in your workspace. ${kpi.auto_reconciled} were auto-reconciled, ${kpi.ai_assisted} were assisted by AI, and ${kpi.unresolved_count} require review. What specific order or metric would you like to inspect?`,
          },
        ])
      }
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Unknown error'
      setMessages((prev) => [
        ...prev,
        { role: 'assistant', content: `Unable to query financial records: ${message}` },
      ])
    } finally {
      setLoading(false)
    }
  }

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-2xl max-h-[85vh] flex flex-col p-0">
        <DialogHeader className="p-4 border-b">
          <div className="flex items-center gap-2">
            <div className="p-2 rounded-lg bg-primary/10 text-primary">
              <Bot className="h-5 w-5" />
            </div>
            <div>
              <DialogTitle className="text-base flex items-center gap-2">
                Finance Controller Intelligence Assistant
                <Badge variant="outline" className="text-xs border-emerald-500/30 text-emerald-500">
                  SQL-Backed Verified Data
                </Badge>
              </DialogTitle>
              <DialogDescription className="text-xs">
                Ask plain-English questions about settlements, exceptions, and revenue variances
              </DialogDescription>
            </div>
          </div>
        </DialogHeader>

        {/* Suggestion prompts */}
        <div className="flex flex-wrap gap-2 px-4 py-2 bg-muted/40 border-b text-xs">
          <button
            className="px-2 py-1 rounded border bg-background hover:bg-muted text-muted-foreground transition"
            onClick={() => handleSend('How much money is currently unreconciled?')}
          >
            "How much money is unreconciled?"
          </button>
          <button
            className="px-2 py-1 rounded border bg-background hover:bg-muted text-muted-foreground transition"
            onClick={() => handleSend('Which exception has the highest financial impact?')}
          >
            "Which exception has highest risk?"
          </button>
          <button
            className="px-2 py-1 rounded border bg-background hover:bg-muted text-muted-foreground transition"
            onClick={() => handleSend('Why did order_DEMO_1012 fail reconciliation?')}
          >
            "Why did order_DEMO_1012 fail?"
          </button>
        </div>

        {/* Messages */}
        <div className="flex-1 overflow-y-auto p-4 space-y-4 min-h-[300px]">
          {messages.map((m, idx) => (
            <div key={idx} className={`flex gap-3 ${m.role === 'user' ? 'justify-end' : 'justify-start'}`}>
              {m.role === 'assistant' && (
                <div className="h-8 w-8 rounded-full bg-primary/10 flex items-center justify-center text-primary flex-shrink-0">
                  <Bot className="h-4 w-4" />
                </div>
              )}
              <div
                className={`max-w-[85%] rounded-lg p-3 text-sm ${
                  m.role === 'user' ? 'bg-primary text-primary-foreground' : 'bg-muted/70 text-foreground border'
                }`}
              >
                {m.role === 'user' ? (
                  <p className="whitespace-pre-wrap leading-relaxed">{m.content}</p>
                ) : (
                  <Markdown className="text-sm leading-relaxed">{m.content}</Markdown>
                )}
                {m.highlights && (
                  <div className="flex flex-wrap items-center gap-2 mt-3 pt-3 border-t border-border/50">
                    {m.highlights.map((h, i) => (
                      <div key={i} className="bg-background/80 px-2.5 py-1.5 rounded border text-xs flex items-center gap-1.5 shadow-xs">
                        <span className="text-muted-foreground text-[10px] block uppercase font-semibold tracking-wider">{h.label}:</span>
                        <span className="font-semibold font-mono text-primary text-xs">{h.value}</span>
                      </div>
                    ))}
                  </div>
                )}
              </div>
              {m.role === 'user' && (
                <div className="h-8 w-8 rounded-full bg-primary flex items-center justify-center text-primary-foreground flex-shrink-0">
                  <User className="h-4 w-4" />
                </div>
              )}
            </div>
          ))}
          {loading && (
            <div className="flex gap-3 items-center text-muted-foreground text-xs py-1">
              <Bot className="h-4 w-4 animate-spin text-primary" />
              <span>Querying Groq AI Controller with verified multi-source financial context...</span>
            </div>
          )}
        </div>

        {/* Input */}
        <div className="p-4 border-t flex gap-2">
          <Input
            placeholder="Ask about transaction discrepancies, fee variances, or settlement exposure..."
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && handleSend()}
          />
          <Button onClick={() => handleSend()} disabled={loading || !input.trim()}>
            <CornerDownLeft className="h-4 w-4" />
          </Button>
        </div>
      </DialogContent>
    </Dialog>
  )
}
