import type { DetailedHTMLProps, HTMLAttributes } from 'react'

/**
 * Ambient typing for the official ElevenLabs ConvAI custom element.
 *
 * The element is registered at runtime by the vendored script at
 * `/widget/convai-widget-embed.js` (see components/anna-embed-widget.tsx),
 * so JSX has no compiler knowledge of it. Declaring it here keeps the
 * widget fully typed instead of falling back to `<any>` / `as any` casts.
 */

/** Public imperative API exposed by `<elevenlabs-convai>`. */
export interface ElevenLabsConvaiElement extends HTMLElement {
  /** Opens the conversation panel (preferred API, newer widget builds). */
  show?: () => void | Promise<void>
  /** Legacy alias for `show()` in older widget builds. */
  open?: () => void | Promise<void>
}

declare module 'react' {
  namespace JSX {
    interface IntrinsicElements {
      'elevenlabs-convai': DetailedHTMLProps<HTMLAttributes<HTMLElement>, HTMLElement> & {
        'agent-id'?: string
        'signed-url'?: string
        /** JSON-encoded object passed to the agent as dynamic variables. */
        'dynamic-variables'?: string
      }
    }
  }
}

declare global {
  interface HTMLElementTagNameMap {
    'elevenlabs-convai': ElevenLabsConvaiElement
  }
}
