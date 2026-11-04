import 'react'

// Type declaration for the ElevenLabs ConvAI custom element, loaded by public/widget/convai-widget-embed.js.
declare module 'react' {
  namespace JSX {
    interface IntrinsicElements {
      'elevenlabs-convai': React.DetailedHTMLProps<React.HTMLAttributes<HTMLElement>, HTMLElement> & {
        'agent-id'?: string
        'signed-url'?: string
        'dynamic-variables'?: string
      }
    }
  }
}
