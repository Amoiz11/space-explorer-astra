import { Component, type ErrorInfo, type ReactNode } from 'react'
import ErrorState from './ErrorState'

interface Props {
  name?: string
  children: ReactNode
}

interface State {
  hasError: boolean
  error: Error | null
}

export default class PanelErrorBoundary extends Component<Props, State> {
  public state: State = {
    hasError: false,
    error: null,
  }

  public static getDerivedStateFromError(error: Error): State {
    return { hasError: true, error }
  }

  public componentDidCatch(error: Error, errorInfo: ErrorInfo) {
    console.error(`PanelErrorBoundary caught an error in ${this.props.name ?? 'Panel'}:`, error, errorInfo)
  }

  public render() {
    if (this.state.hasError) {
      return (
        <div className="my-2">
          <ErrorState
            message={`${this.props.name ? `[${this.props.name}] ` : ''}${this.state.error?.message || 'Component failed to render'}`}
            onRetry={() => this.setState({ hasError: false, error: null })}
          />
        </div>
      )
    }

    return this.props.children
  }
}
