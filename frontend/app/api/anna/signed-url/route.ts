import { NextRequest, NextResponse } from 'next/server'

// Public agent identifier, used when ELEVENLABS_AGENT_ID is not set.
const DEFAULT_AGENT_ID = 'agent_8401m0n03cggfgebhfh0cj96t7aj'
const SUPPORTED_LANGUAGES = ['pl', 'en'] as const

/**
 * Returns a signed URL for the Anna conversational agent.
 *
 * The ElevenLabs API key stays on the server: the browser only receives a
 * short-lived signed URL, which already encodes the agent and the session
 * signature. The `lang` query parameter is echoed back so the client can
 * keep the conversation in the guest's active language.
 */
export async function GET(req: NextRequest) {
  const apiKey = process.env.ELEVENLABS_API_KEY
  const agentId = process.env.ELEVENLABS_AGENT_ID || DEFAULT_AGENT_ID

  const requestedLang = new URL(req.url).searchParams.get('lang')
  const lang = SUPPORTED_LANGUAGES.find((code) => code === requestedLang) ?? 'en'

  if (!apiKey) {
    return NextResponse.json(
      { error: 'ELEVENLABS_API_KEY is not configured on the server' },
      { status: 500 },
    )
  }

  const url =
    'https://api.elevenlabs.io/v1/convai/conversation/get-signed-url?' +
    new URLSearchParams({ agent_id: agentId }).toString()

  try {
    const res = await fetch(url, {
      headers: { 'xi-api-key': apiKey },
      cache: 'no-store',
    })
    if (!res.ok) {
      return NextResponse.json(
        { error: `ElevenLabs signed-url request failed with status ${res.status}` },
        { status: 502 },
      )
    }

    const data = (await res.json()) as { signed_url?: string }
    if (!data.signed_url) {
      return NextResponse.json({ error: 'ElevenLabs response has no signed_url' }, { status: 502 })
    }

    return NextResponse.json({
      signed_url: data.signed_url,
      language: lang,
    })
  } catch (err) {
    return NextResponse.json(
      { error: err instanceof Error ? err.message : 'Unknown error' },
      { status: 502 },
    )
  }
}
