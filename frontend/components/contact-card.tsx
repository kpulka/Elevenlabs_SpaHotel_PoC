import type { LucideIcon } from 'lucide-react'
import type { ReactNode } from 'react'

type ContactCardProps = {
  icon: LucideIcon
  title: string
  children: ReactNode
}

export function ContactCard({ icon: Icon, title, children }: ContactCardProps) {
  return (
    <div className="rounded-2xl border border-gold/20 bg-cream p-6">
      <div className="flex items-center gap-3">
        <Icon className="size-6 text-sage" aria-hidden="true" />
        <h2 className="font-serif text-lg font-semibold text-navy">{title}</h2>
      </div>
      {children}
    </div>
  )
}
