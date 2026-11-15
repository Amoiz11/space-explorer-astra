import GlassCard from './GlassCard'

type Props = { message: string; onRetry: () => void }

export default function ErrorState({ message, onRetry }: Props) {
  return (
    <GlassCard>
      <p className="text-[var(--blocked)]">Something went wrong: {message}</p>
      <button onClick={onRetry} className="btn btn-secondary mt-4">Retry</button>
    </GlassCard>
  )
}
