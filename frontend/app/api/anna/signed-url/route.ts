import { NextRequest, NextResponse } from 'next/server'

// zwraca signed-url dla agenta Anna — bez wystawiania klucza w przeglądarce.
// Signed URL zawiera podpisany dostęp do rozmowy (agent_id + conversation_signature).
export async function GET(req: NextRequest) {
  // ID agenta konfigurowane przez env; literał to udokumentowany fallback dla dev/demo.
  const agentId = process.env.ELEVENLABS_AGENT_ID ?? 'agent_8401m0n03cggfgebhfh0cj96t7aj'
  const apiKey = process.env.ELEVENLABS_API_KEY
  const { searchParams } = new URL(req.url)
  const lang = searchParams.get('lang') || 'pl'

  if (!apiKey) {
    return NextResponse.json(
      { error: 'ELEVENLABS_API_KEY not set on server' },
      { status: 500 },
    )
  }

  const url = `https://api.elevenlabs.io/v1/convai/conversation/get-signed-url?agent_id=${agentId}`
  try {
    const res = await fetch(url, {
      headers: { 'xi-api-key': apiKey },
      cache: 'no-store',
    })
    if (!res.ok) {
      // Szczegóły zostają po stronie serwera — klient dostaje krótki, ogólny komunikat.
      const body = await res.text().catch(() => '')
      console.error(
        `ElevenLabs signed-url failed (agent ${agentId}): HTTP ${res.status} ${body.slice(0, 500)}`,
      )
      return NextResponse.json({ error: 'Voice assistant is temporarily unavailable' }, { status: 502 })
    }
    const data = (await res.json()) as { signed_url?: string }
    if (!data.signed_url) {
      return NextResponse.json({ error: 'No signed_url in response' }, { status: 502 })
    }
    return NextResponse.json({
      signed_url: data.signed_url,
      language: lang,
    })
  } catch (err) {
    // Surowy błąd tylko do logów serwera; klient nie widzi wewnętrznych szczegółów.
    console.error('ElevenLabs signed-url request failed:', err)
    return NextResponse.json({ error: 'Voice assistant is temporarily unavailable' }, { status: 502 })
  }
}