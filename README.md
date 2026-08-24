# ElevenLabs — Deployment Strategist: Case Study „Wirtualny Recepcjonista AI"

**Uzdrowisko Termalne „Bukowy Dwór", Krynica-Zdrój** — agent głosowy **Anna** (ElevenLabs Conversational AI) obsługujący seniorów 60+: rezerwacje SPA, pokoje, procedury operacyjne, eskalacja do człowieka.

## Architektura (stan aktualny 2026-08)

| Warstwa | Technologia | Szczegóły |
|---|---|---|
| **Agent** | ElevenLabs Conversational AI | `agent_8401m0n03cggfgebhfh0cj96t7aj` |
| **LLM** | `gemini-3.5-flash-lite` | nowy, szybki, tani; temp 0.1 |
| **Głos** | Jessica (`cgSgspJ2msm6clMCkdW9`) | `eleven_v3_conversational`, speed 0.85, stability 0.8 |
| **Prompt** | `docs/anna_system_prompt_v3.md` (wgrany) | 8 679 zn., sekcja PROCEDURY OPERACYJNE |
| **Workflow** | graf v3 | `start → main_agent → end` (naprawiony dead-end) |
| **Procedures** | 7 opublikowanych | anulacja SPA, zmiana terminu, zwrot zadatku, early/late, dieta, transport, reklamacje |
| **Narzędzia** | 5 webhooków | check_spa, book_spa, check_room, send_sms, transfer_to_simulated_handoff |
| **RAG** | 5 plików KB | `docs/baza_wiedzy_rag_bukowy_dwor/` (tryby prompt/auto) |
| **Backend** | FastAPI (`mock_backend/`) | symulacja PMS, port **8011** (8000 zajęty przez system) |
| **Frontend** | Next.js (`frontend/`) | widget `<elevenlabs-convai>` (self-host CDN), signed-url |
| **Tunel** | cloudflared trycloudflare | auto-update hosts + webhooki po restarcie |

## 🚀 Szybki start (demo na żądanie)

### Opcja A — kontener Podman (rekomendowana)
```bash
cd mock_backend/tunnel
./podman_start.sh    # kontener + tunel + hosts + webhooki (~15s)
# ... pokaz ...
./podman_stop.sh     # gasi wszystko (~3s)
```

### Opcja B — proces Python
```bash
cd mock_backend/tunnel
./start_anna.sh      # uvicorn + tunel + hosts + webhooki
```

Oba skrypty robią to samo: **backend → tunel → wpis w hosts → aktualizacja 5 webhooków agenta na nowy URL**. Po restarcie komputera autostart (on-logon) odpala `start_anna.sh` automatycznie.

## 🧪 Test po starcie
```bash
curl -X POST "https://<URL_z_skryptu>/check_room_availability" \
  -H "Content-Type: application/json" \
  -d '{"room_type":"dwuosobowy","check_in":"2026-08-24","check_out":"2026-08-26"}'
# → {"available":true,"total_price":1000,...}
```

## 🖥️ Frontend (widget)
```bash
cd frontend
pnpm install && pnpm dev   # http://localhost:3030
```
Wymaga `frontend/.env.local` z `ELEVENLABS_API_KEY` (nie ma go w repo — utwórz lokalnie).

## 📦 Instalacja na nowym komputerze
1. `git clone https://github.com/kpulka/Elevenlabs_SpaHotel_PoC.git`
2. Utwórz `frontend/.env.local` z kluczem: `ELEVENLABS_API_KEY=sk_...`
3. Pobierz cloudflared do `mock_backend/tunnel/`:
   `curl -L -o cloudflared.exe https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-windows-amd64.exe`
4. `cd mock_backend/tunnel && ./podman_start.sh` (lub `start_anna.sh`)
5. **Wymagany admin** do zapisu wpisu w hosts (omija problem DNS routera bez A-rekordów).

## 🗺️ Mapa repozytorium (kluczowe)
```
├── .planning/              # GSD: ROADMAP (epiki A–J), PROJECT.md, phases/, workflow/
├── mock_backend/           # FastAPI (PMS mock) + tunnel/ (skrypty, Dockerfile)
├── frontend/               # Next.js widget
├── docs/                   # prompty, specyfikacje, KB, audyt, procedury, workflow
├── presentation/           # PPTX (PL/EN), deck HTML, narracja demo
└── README.md               # ten plik
```

## 📚 Dokumentacja (ważne pliki)
- `.planning/ROADMAP.md` — pełna historia GSD: epiki A–J (od przygotowania po procedures/workflow/odporność)
- `docs/audyt_agenta_2026-08.md` — audyt agenta + sekcje handoff/workflow/procedures
- `docs/elevenlabs_agent_workflow.md` — diagram workflow (mermaid) + implementacja
- `docs/elevenlabs_agent_procedures.md` — 7 procedur operacyjnych (SOP)
- `docs/anna_system_prompt_v3.md` — aktualny system prompt
- `mock_backend/README.md` — endpointy backendu
- `presentation/03_narracja_demo.md` — skrypt 3 ścieżek demo

## ⚠️ Znane ograniczenia (PoC)
- **Ulotny tunel** trycloudflare — URL zmienia się po restarcie; skrypty auto-naprawiają, ale stały adres wymaga domeny + named tunnel (Cloudflare).
- **Telefonia** nieaktywna (`phone_numbers: []`) — agent działa przez widget webowy; handoff symulowany (`transfer_to_simulated_handoff`), nie `transfer_to_number`.
- **Procedury** — opublikowane i aktywne w realnych rozmowach; symulacja API ich nie testuje (ograniczenie narzędzia).
- **Port 8000** zajęty przez proces systemowy (svchost) — backend działa na **8011**.

## 🔑 Kluczowe ID
- Agent: `agent_8401m0n03cggfgebhfh0cj96t7aj` · Branch: `agtbrch_9601m0n03dege4yvwseypec1hm81`
- Więcej w `.planning/AGENT_ID.txt`
