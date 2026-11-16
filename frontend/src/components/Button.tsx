import React, { forwardRef } from 'react'
import { Link, type LinkProps } from 'react-router-dom'

export type ButtonVariant = 'primary' | 'secondary' | 'ghost'
export type ButtonSize = 'sm' | 'md' | 'lg'

export interface BaseButtonProps {
  variant?: ButtonVariant
  size?: ButtonSize
  className?: string
  children?: React.ReactNode
  icon?: React.ReactNode
}

export type ButtonProps = BaseButtonProps &
  (
    | ({ to: LinkProps['to'] } & Omit<LinkProps, 'to'>)
    | ({ href: string } & React.AnchorHTMLAttributes<HTMLAnchorElement>)
    | ({ to?: undefined; href?: undefined } & React.ButtonHTMLAttributes<HTMLButtonElement>)
  )

export const Button = forwardRef<HTMLButtonElement | HTMLAnchorElement, ButtonProps>(
  ({ variant = 'primary', size = 'md', className = '', children, icon, ...props }, ref) => {
    const sizeClasses = {
      sm: 'px-3 py-1.5 text-xs rounded-lg gap-1.5',
      md: 'px-4 py-2 text-sm rounded-xl gap-2',
      lg: 'px-6 py-3 text-base rounded-2xl gap-2.5',
    }[size]

    const variantClasses = {
      primary:
        'btn-primary bg-gradient-to-r from-[#4DA3FF] to-[#2563EB] text-[#05070D] font-semibold border border-white/20 shadow-[inset_0_1px_0_rgba(255,255,255,0.4),0_4px_18px_rgba(77,163,255,0.3)] hover:shadow-[inset_0_1px_0_rgba(255,255,255,0.6),0_6px_24px_rgba(77,163,255,0.45)] hover:brightness-110 active:scale-[0.98]',
      secondary:
        'btn-secondary bg-white/[0.05] border border-white/10 text-[var(--text-1)] backdrop-blur-md shadow-[inset_0_1px_0_rgba(255,255,255,0.08),0_4px_12px_rgba(0,0,0,0.25)] hover:border-white/25 hover:bg-white/[0.09] active:scale-[0.98]',
      ghost:
        'btn-ghost bg-transparent text-[var(--text-2)] hover:text-white hover:bg-white/[0.06] border border-transparent active:scale-[0.98]',
    }[variant]

    const baseClasses = `inline-flex items-center justify-center font-medium transition-all duration-150 cursor-pointer select-none focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[var(--earth)] focus-visible:ring-offset-2 focus-visible:ring-offset-[var(--bg-0)] disabled:opacity-40 disabled:cursor-not-allowed disabled:pointer-events-none ${sizeClasses} ${variantClasses} ${className}`

    if ('to' in props && props.to) {
      const { to, ...rest } = props
      return (
        <Link ref={ref as React.ForwardedRef<HTMLAnchorElement>} to={to} className={baseClasses} {...rest}>
          {icon}
          {children}
        </Link>
      )
    }

    if ('href' in props && props.href) {
      const { href, ...rest } = props
      return (
        <a ref={ref as React.ForwardedRef<HTMLAnchorElement>} href={href} className={baseClasses} {...rest}>
          {icon}
          {children}
        </a>
      )
    }

    const { type = 'button', ...rest } = props as React.ButtonHTMLAttributes<HTMLButtonElement>
    return (
      <button ref={ref as React.ForwardedRef<HTMLButtonElement>} type={type} className={baseClasses} {...rest}>
        {icon}
        {children}
      </button>
    )
  }
)

Button.displayName = 'Button'
export default Button
