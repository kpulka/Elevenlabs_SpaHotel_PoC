import { cva, type VariantProps } from 'class-variance-authority'
import Link from 'next/link'
import type { ComponentProps } from 'react'

import { cn } from '@/lib/utils'

const hotelButtonVariants = cva(
  'inline-flex min-h-[52px] items-center justify-center gap-2 whitespace-nowrap rounded-lg px-8 text-base font-medium transition-colors duration-150 outline-none focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-gold disabled:pointer-events-none disabled:opacity-40',
  {
    variants: {
      variant: {
        primary: 'bg-navy text-white hover:bg-navy/90',
        secondary: 'border-2 border-gold bg-transparent text-navy hover:bg-gold/10',
        ghost: 'border-2 border-white bg-transparent text-white hover:bg-white/10',
        danger: 'bg-error text-white hover:bg-error/90',
      },
      fullWidth: {
        true: 'w-full',
        false: '',
      },
    },
    defaultVariants: {
      variant: 'primary',
      fullWidth: false,
    },
  },
)

type HotelButtonProps = VariantProps<typeof hotelButtonVariants> & {
  href?: string
  className?: string
} & (ComponentProps<'button'> | ComponentProps<typeof Link>)

export function HotelButton({
  href,
  variant,
  fullWidth,
  className,
  children,
  ...props
}: HotelButtonProps) {
  const classes = cn(hotelButtonVariants({ variant, fullWidth }), className)

  if (href) {
    return (
      <Link href={href} className={classes} {...(props as ComponentProps<typeof Link>)}>
        {children}
      </Link>
    )
  }

  return (
    <button className={classes} {...(props as ComponentProps<'button'>)}>
      {children}
    </button>
  )
}
