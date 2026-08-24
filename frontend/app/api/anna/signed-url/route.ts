import { NextResponse } from 'next/server'

// zwraca signed-url dla agenta Anna — bez wystawiania klucza w przeglądarce.
// Signed URL zawiera podpisany dostęp do rozmowy (agent_id + conversation_signature),
// nie jest tajemnicą, ale nie chcemy trzymać API key po stronie klienta.
export async function GET() {
  const agentId = 'agent_8401m0n03cggfgebhfh0cj96t7aj'
  const apiKey = process.env.ELEVENLABS_API_KEY

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
      return NextResponse.json(
        { error: `ElevenLabs signed-url failed: ${res.status}` },
        { status: 502 },
      )
    }
    const data = (await res.json()) as { signed_url?: string }
    if (!data.signed_url) {
      return NextResponse.json({ error: 'No signed_url in response' }, { status: 502 })
    }
    return NextResponse.json({ signed_url: data.signed_url })
  } catch (err) {
    return NextResponse.json(
      { error: err instanceof Error ? err.message : 'unknown' },
      { status: 502 },
    )
  }
}