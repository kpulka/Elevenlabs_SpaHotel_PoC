import os
import sys
from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN
from pptx.enum.shapes import MSO_SHAPE

def create_presentation():
    prs = Presentation()
    # 16:9 widescreen
    prs.slide_width = Inches(13.333)
    prs.slide_height = Inches(7.5)

    NAVY = RGBColor(27, 42, 74)       # #1B2A4A
    GOLD = RGBColor(201, 168, 76)     # #C9A84C
    CREAM = RGBColor(245, 240, 232)   # #F5F0E8
    WHITE = RGBColor(255, 255, 255)
    CHARCOAL = RGBColor(44, 44, 44)   # #2C2C2C
    SAGE = RGBColor(122, 158, 126)    # #7A9E7E
    MUTED = RGBColor(138, 138, 138)

    blank_layout = prs.slide_layouts[6]
    assets_dir = os.path.join(os.path.dirname(__file__), 'assets')

    def add_bg(slide, color=NAVY):
        bg = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, 0, 0, prs.slide_width, prs.slide_height)
        bg.fill.solid()
        bg.fill.fore_color.rgb = color
        bg.line.fill.background()
        return bg

    def add_header(slide, title_text, category_text="ELEVENLABS DEPLOYMENT STRATEGIST CASE STUDY", dark_theme=True):
        # Category tag
        cat_box = slide.shapes.add_textbox(Inches(0.8), Inches(0.5), Inches(11.7), Inches(0.4))
        tf_cat = cat_box.text_frame
        tf_cat.word_wrap = True
        p_cat = tf_cat.paragraphs[0]
        p_cat.text = category_text.upper()
        p_cat.font.size = Pt(11)
        p_cat.font.bold = True
        p_cat.font.color.rgb = GOLD
        p_cat.font.name = 'Arial'

        # Title
        title_box = slide.shapes.add_textbox(Inches(0.8), Inches(0.85), Inches(11.7), Inches(0.9))
        tf_title = title_box.text_frame
        tf_title.word_wrap = True
        p_title = tf_title.paragraphs[0]
        p_title.text = title_text
        p_title.font.size = Pt(28)
        p_title.font.bold = True
        p_title.font.color.rgb = WHITE if dark_theme else NAVY
        p_title.font.name = 'Georgia'

    def add_notes(slide, notes_text):
        notes_slide = slide.notes_slide
        tf = notes_slide.notes_text_frame
        tf.text = notes_text

    # ----------------------------------------------------
    # SLIDE 1: Title
    # ----------------------------------------------------
    s1 = prs.slides.add_slide(blank_layout)
    add_bg(s1, NAVY)

    # Decorative gold line
    line = s1.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(0.8), Inches(1.8), Inches(1.5), Inches(0.06))
    line.fill.solid()
    line.fill.fore_color.rgb = GOLD
    line.line.fill.background()

    tb = s1.shapes.add_textbox(Inches(0.8), Inches(2.1), Inches(7.5), Inches(3.2))
    tf = tb.text_frame
    tf.word_wrap = True
    p1 = tf.paragraphs[0]
    p1.text = "Wirtualny Recepcjonista AI"
    p1.font.size = Pt(38)
    p1.font.bold = True
    p1.font.color.rgb = WHITE
    p1.font.name = 'Georgia'

    p2 = tf.add_paragraph()
    p2.text = "Uzdrowisko Termalne „Bukowy Dwór” × ElevenLabs"
    p2.font.size = Pt(22)
    p2.font.color.rgb = GOLD
    p2.font.name = 'Georgia'

    p3 = tf.add_paragraph()
    p3.text = "\nWdrożenie natywnego agenta konwersacyjnego dla wymagającej grupy seniorów 60+ w sieci resortów SPA."
    p3.font.size = Pt(14)
    p3.font.color.rgb = CREAM

    # Bottom badge
    bb = s1.shapes.add_textbox(Inches(0.8), Inches(6.2), Inches(10), Inches(0.6))
    p_b = bb.text_frame.paragraphs[0]
    p_b.text = "Etap V1 & V2: Case Study, Product Design & System Architecture | 2026"
    p_b.font.size = Pt(12)
    p_b.font.color.rgb = SAGE

    # Right side image
    img1 = os.path.join(assets_dir, 'anna_widget_desktop.jpg')
    if os.path.exists(img1):
        s1.shapes.add_picture(img1, Inches(8.0), Inches(1.4), Inches(4.7))

    add_notes(s1, "Zacznij od 30 sekund kontekstu biznesowego: dlaczego uzdrowisko i dlaczego seniorzy, zanim wejdziesz w technikę.")

    # ----------------------------------------------------
    # SLIDE 2: Problem
    # ----------------------------------------------------
    s2 = prs.slides.add_slide(blank_layout)
    add_bg(s2, CREAM)
    add_header(s2, "Senior czeka. Recepcja nie odbiera.", "WYZWANIE BIZNESOWE", dark_theme=False)

    # 4 Cards for pain points
    cards_data = [
        ("60–70% Gości to Seniorzy", "Grupa 60+ preferuje tradycyjny kontakt telefoniczny ponad aplikacje i formularze webowe.", "📞"),
        ("Szczyt Ruchu = Utracone Połączenia", "Kumulacja telefonów w godzinach 8:00–10:00 i 16:00–18:00 generuje zajęte linie i frustrację.", "⏰"),
        ("Utracony Przychód ze SPA", "Niedoczekany telefon to brak rezerwacji zabiegu (80–160 PLN) lub pokoju (350–750 PLN).", "💰"),
        ("Brak Proaktywności Recepcji", "Personel jest przeciążony meldowaniem i nie wykonuje telefonów outbound przed przyjazdem.", "👥")
    ]

    for i, (head, desc, icon) in enumerate(cards_data):
        row = i // 2
        col = i % 2
        left = Inches(0.8 + col * 5.9)
        top = Inches(1.9 + row * 2.5)
        
        box = s2.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, left, top, Inches(5.6), Inches(2.2))
        box.fill.solid()
        box.fill.fore_color.rgb = WHITE
        box.line.color.rgb = GOLD
        box.line.width = Pt(1)

        tb = s2.shapes.add_textbox(left + Inches(0.3), top + Inches(0.2), Inches(5.0), Inches(1.8))
        tf = tb.text_frame
        tf.word_wrap = True
        p = tf.paragraphs[0]
        p.text = f"{icon}  {head}"
        p.font.size = Pt(17)
        p.font.bold = True
        p.font.color.rgb = NAVY
        p.font.name = 'Georgia'

        p_desc = tf.add_paragraph()
        p_desc.text = f"\n{desc}"
        p_desc.font.size = Pt(13)
        p_desc.font.color.rgb = CHARCOAL

    add_notes(s2, "To slajd o problemie biznesowym. Zanim powiesz jak to rozwiązałeś — zapytaj rekrutera, jakie mają pytania do problemu.")

    # ----------------------------------------------------
    # SLIDE 3: Persona
    # ----------------------------------------------------
    s3 = prs.slides.add_slide(blank_layout)
    add_bg(s3, NAVY)
    add_header(s3, "Kto dzwoni? Pani Zofia, 72 lata.", "USER PERSONA & EMPATHY", dark_theme=True)

    img_zofia = os.path.join(assets_dir, 'persona_zofia.png')
    if os.path.exists(img_zofia):
        s3.shapes.add_picture(img_zofia, Inches(0.8), Inches(1.9), Inches(4.2))

    tb3 = s3.shapes.add_textbox(Inches(5.3), Inches(1.8), Inches(7.2), Inches(5.0))
    tf3 = tb3.text_frame
    tf3.word_wrap = True

    persona_points = [
        ("Profil i Mowa:", "Mówi spokojnie, robi naturalne pauzy w środku zdania, zastanawia się nad odpowiedziami."),
        ("Bariery Pamięciowe:", "Nie pamięta nazw medycznych zabiegów — pyta o „ten masaż co pomaga na lędźwie”."),
        ("Niska Tolerancja na Błędy:", "Gdy bot wchodzi w słowo lub nie rozumie 2 razy — senior natychmiast odkłada słuchawkę."),
        ("Potrzeba Potwierdzenia:", "Oczekuje przejrzystego SMS-a z podsumowaniem, często z prośbą o wysyłkę do córki."),
        ("Wniosek Projektowy:", "Każdy parametr techniczny (timeout 3s, tempo 0.85x, parafrazowanie) wynika wprost z tej persony.")
    ]

    for i, (title_p, body_p) in enumerate(persona_points):
        p = tf3.paragraphs[0] if i == 0 else tf3.add_paragraph()
        p.text = f"• {title_p} "
        p.font.bold = True
        p.font.size = Pt(14)
        p.font.color.rgb = GOLD
        
        # Add normal text
        run = p.add_run()
        run.text = body_p
        run.font.bold = False
        run.font.color.rgb = WHITE
        run.font.size = Pt(14)

    add_notes(s3, "Podkreśl: to nie jest abstrakcyjna persona. To prototyp pacjenta sanatoryjnego w Polsce.")

    # ----------------------------------------------------
    # SLIDE 4: Architecture & Loop
    # ----------------------------------------------------
    s4 = prs.slides.add_slide(blank_layout)
    add_bg(s4, NAVY)
    add_header(s4, "Natywna pętla konwersacyjna ElevenLabs", "SYSTEM ARCHITECTURE (HIGH LEVEL)", dark_theme=True)

    img_arch = os.path.join(assets_dir, 'diagram_architecture.png')
    if os.path.exists(img_arch):
        s4.shapes.add_picture(img_arch, Inches(0.8), Inches(1.8), Inches(7.5))

    tb4 = s4.shapes.add_textbox(Inches(8.5), Inches(1.8), Inches(4.3), Inches(5.0))
    tf4 = tb4.text_frame
    tf4.word_wrap = True

    p4_1 = tf4.paragraphs[0]
    p4_1.text = "Pojedynczy silnik vs Kaskada"
    p4_1.font.size = Pt(18)
    p4_1.font.bold = True
    p4_1.font.color.rgb = GOLD

    p4_desc = tf4.add_paragraph()
    p4_desc.text = "\n• Zintegrowana pętla: STT + LLM + TTS w jednym kanale WebRTC/SIP\n\n• Czas reakcji: ~430 ms zamiast >2.0s w klasycznym kaskadowym backendzie\n\n• Strict Grounding: Odpowiedzi wyłącznie w oparciu o 5 plików RAG\n\n• Tool Calling: Natywne webhooki do systemu hotelowego PMS\n\n• Deterministic Handoff: Przełączanie na recepcję w razie wątpliwości"
    p4_desc.font.size = Pt(13)
    p4_desc.font.color.rgb = WHITE

    add_notes(s4, "Dlaczego natywny ElevenLabs? Eliminacja latencji. Kaskada 3 osobnych serwisów gubi seniora przez 2-sekundową ciszę.")

    # ----------------------------------------------------
    # SLIDE 5: 3 Decisions
    # ----------------------------------------------------
    s5 = prs.slides.add_slide(blank_layout)
    add_bg(s5, CREAM)
    add_header(s5, "3 kluczowe decyzje architektoniczne", "STRATEGIC TRADE-OFFS", dark_theme=False)

    decisions = [
        ("1. Natywny Agent (vs Custom LLM)", "Kaskadowy pipeline (STT -> zewnętrzny LLM -> TTS) generuje ponad 2s opóźnienia. Natywna pętla ElevenLabs schodzi do ~430ms. Dla seniora każda sekunda ciszy to utrata zaufania."),
        ("2. Eleven v3 (vs Flash 75ms)", "Flash jest ultra-szybki, ale brzmi technicznie. Eleven v3 Conversational (280ms) oferuje ciepło, intonację i empatię. Dla gościa 70+ naturalność głosu jest ważniejsza niż 100ms."),
        ("3. UX Parametry: 3.0s & Patient", "Domyślny timeout 1.2s powoduje wchodzenie w słowo, gdy senior bierze oddech. Ustawienie turn_timeout: 3.0s, turn_eagerness: Patient i speed: 0.85x eliminuje stres.")
    ]

    for i, (d_title, d_desc) in enumerate(decisions):
        top = Inches(1.9 + i * 1.7)
        box = s5.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(0.8), top, Inches(11.7), Inches(1.5))
        box.fill.solid()
        box.fill.fore_color.rgb = WHITE
        box.line.color.rgb = GOLD

        tb = s5.shapes.add_textbox(Inches(1.1), top + Inches(0.15), Inches(11.1), Inches(1.2))
        tf = tb.text_frame
        tf.word_wrap = True
        p = tf.paragraphs[0]
        p.text = d_title
        p.font.size = Pt(16)
        p.font.bold = True
        p.font.color.rgb = NAVY

        p_b = tf.add_paragraph()
        p_b.text = d_desc
        p_b.font.size = Pt(12)
        p_b.font.color.rgb = CHARCOAL

    add_notes(s5, "Podkreśl, że jesteś świadom kosztu i trade-offów: wiesz kiedy wybrać Flash, a dlaczego w sanatorium wygrywa v3.")

    # ----------------------------------------------------
    # SLIDE 6: Baza Wiedzy (RAG)
    # ----------------------------------------------------
    s6 = prs.slides.add_slide(blank_layout)
    add_bg(s6, NAVY)
    add_header(s6, "Baza Wiedzy (RAG) i Strict Grounding", "KNOWLEDGE BASE & ZERO HALUCYNACJI", dark_theme=True)

    # Two columns
    box_l = s6.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(0.8), Inches(1.9), Inches(5.6), Inches(5.0))
    box_l.fill.solid()
    box_l.fill.fore_color.rgb = RGBColor(35, 52, 88)
    box_l.line.color.rgb = GOLD

    tb_l = s6.shapes.add_textbox(Inches(1.1), Inches(2.1), Inches(5.0), Inches(4.5))
    tf_l = tb_l.text_frame
    tf_l.word_wrap = True
    p = tf_l.paragraphs[0]
    p.text = "Struktura 5 Plików Markdown"
    p.font.size = Pt(18)
    p.font.bold = True
    p.font.color.rgb = GOLD

    rag_text = "\n• 01_dojazd.md — parking, meleks, brak barier\n• 02_katalog_spa.md — 7 zabiegów i baseny\n• 03_pokoje_i_cennik.md — 3 typy pokoi\n• 04_restauracja.md — diety cukrzycowa, lekkostrawna\n• 05_procedury.md — regulamin i bezpieczeństwo\n\nPodział trybów RAG:\n• Prompt Mode (w kontekście): cennik + procedury\n• Auto Mode (semantic search): opisy i dojazd"
    p2 = tf_l.add_paragraph()
    p2.text = rag_text
    p2.font.size = Pt(13)
    p2.font.color.rgb = WHITE

    box_r = s6.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(6.9), Inches(1.9), Inches(5.6), Inches(5.0))
    box_r.fill.solid()
    box_r.fill.fore_color.rgb = RGBColor(35, 52, 88)
    box_r.line.color.rgb = SAGE

    tb_r = s6.shapes.add_textbox(Inches(7.2), Inches(2.1), Inches(5.0), Inches(4.5))
    tf_r = tb_r.text_frame
    tf_r.word_wrap = True
    p = tf_r.paragraphs[0]
    p.text = "Protokół Medyczny i Bezpieczeństwo"
    p.font.size = Pt(18)
    p.font.bold = True
    p.font.color.rgb = SAGE

    safe_text = "\n• Strict Grounding:\nBrak informacji w bazie = natychmiastowe przekazanie do recepcji. Zakaz zgadywania cen i terminów.\n\n• Wywiad Balneologiczny:\nPrzed zapisem na kąpiel siarczkową lub borowinową agent pyta o przeciwwskazania sercowo-naczyniowe.\n\n• Natychmiastowa Eskalacja:\nSymptomy awaryjne (ból w klatce, duszność) uruchamiają transfer do dyżurki medycznej."
    p2 = tf_r.add_paragraph()
    p2.text = safe_text
    p2.font.size = Pt(13)
    p2.font.color.rgb = WHITE

    add_notes(s6, "W sanatorium błąd w cenie to problem handlowy, ale halucynacja o zabiegu to zagrożenie zdrowotne.")

    # ----------------------------------------------------
    # SLIDE 7: Tools (Table)
    # ----------------------------------------------------
    s7 = prs.slides.add_slide(blank_layout)
    add_bg(s7, CREAM)
    add_header(s7, "Anna nie tylko rozmawia — działa w systemie PMS", "TOOL CALLING & INTEGRACJA", dark_theme=False)

    # Table
    rows = 8
    cols = 3
    table_shape = s7.shapes.add_table(rows, cols, Inches(0.8), Inches(1.9), Inches(11.7), Inches(4.8))
    table = table_shape.table
    table.columns[0].width = Inches(3.2)
    table.columns[1].width = Inches(5.5)
    table.columns[2].width = Inches(3.0)

    headers = ["Narzędzie (Function)", "Rola Biznesowa / Przepływ", "Typ Integracji"]
    for col_idx, h in enumerate(headers):
        cell = table.cell(0, col_idx)
        cell.fill.solid()
        cell.fill.fore_color.rgb = NAVY
        p = cell.text_frame.paragraphs[0]
        p.text = h
        p.font.bold = True
        p.font.color.rgb = GOLD
        p.font.size = Pt(13)

    data = [
        ("check_spa_availability", "Weryfikacja wolnych slotów na zabiegi w kalendarzu", "POST Webhook (FastAPI/PMS)"),
        ("book_spa_appointment", "Zapis gościa na zabieg, wygenerowanie ID (np. SPA-4821)", "POST Webhook (FastAPI/PMS)"),
        ("cancel_spa_appointment", "Anulowanie zabiegu (bezpłatnie >2 h, 50% <2 h, 0% przy zwolnieniu medycznym)", "POST Webhook (FastAPI/PMS)"),
        ("reschedule_spa_appointment", "Zmiana terminu zabiegu (bezpłatna, nowy kod SPA)", "POST Webhook (FastAPI/PMS)"),
        ("check_room_availability", "Sprawdzenie terminów pokoi i kalkulacja ceny pobytu", "POST Webhook (FastAPI/PMS)"),
        ("send_sms_summary", "Wysyłka SMS / Telegram z numerem rezerwacji i wskazówkami", "POST Webhook (Bramka SMS)"),
        ("transfer_to_simulated_handoff", "Przekazanie do recepcji / dyżurki (log + alert Telegram)", "POST Webhook (handoff symulowany — brak SIP)")
    ]

    for row_idx, (c1, c2, c3) in enumerate(data, start=1):
        for col_idx, val in enumerate([c1, c2, c3]):
            cell = table.cell(row_idx, col_idx)
            cell.fill.solid()
            cell.fill.fore_color.rgb = WHITE if row_idx % 2 == 1 else RGBColor(250, 246, 240)
            p = cell.text_frame.paragraphs[0]
            p.text = val
            p.font.size = Pt(12)
            p.font.color.rgb = CHARCOAL

    add_notes(s7, "Zwróć uwagę, że handoff do człowieka jest w PoC symulowany webhookiem (log + alert Telegram), bo nie ma telefonii/SIP — docelowo zastąpi go natywne SIP REFER.")

    # ----------------------------------------------------
    # SLIDE 8: Omnichannel (Phone + Web)
    # ----------------------------------------------------
    s8 = prs.slides.add_slide(blank_layout)
    add_bg(s8, NAVY)
    add_header(s8, "Dwa kanały, jeden zunifikowany asystent", "OMNICHANNEL DEPLOYMENT", dark_theme=True)

    img_chips = os.path.join(assets_dir, 'anna_widget_chips.jpg')
    if os.path.exists(img_chips):
        s8.shapes.add_picture(img_chips, Inches(0.8), Inches(1.8), Inches(3.2))

    tb8 = s8.shapes.add_textbox(Inches(4.3), Inches(1.8), Inches(8.2), Inches(5.0))
    tf8 = tb8.text_frame
    tf8.word_wrap = True

    p = tf8.paragraphs[0]
    p.text = "Kanał 1: Tradycyjna Telefonia (SIP Trunk) — ścieżka docelowa"
    p.font.size = Pt(18)
    p.font.bold = True
    p.font.color.rgb = GOLD

    p_t = tf8.add_paragraph()
    p_t.text = "• Ten sam agent i prompt po podpięciu SIP Trunk (Faza II — telefonii nie ma w PoC)\n• Bezpośredni numer do recepcji hotelu\n• Dostępność 24/7 bez oczekiwania w kolejce\n• Turn timeout 3.0s, parafrazowanie ustaleń, wysyłka SMS po zakończeniu\n"
    p_t.font.size = Pt(13)
    p_t.font.color.rgb = WHITE

    p2 = tf8.add_paragraph()
    p2.text = "Kanał 2: Interaktywny Widget Webowy na Stronie Hotelu"
    p2.font.size = Pt(18)
    p2.font.bold = True
    p2.font.color.rgb = SAGE

    p_w = tf8.add_paragraph()
    p_w.text = "• Quick Reply Chips: Szybki wybór języka (6 opcji) i tematów rozmowy\n• Live Transkrypcja: Wizualne śledzenie rozmowy w czasie rzeczywistym\n• Karta Sukcesu: Natychmiastowe potwierdzenie rezerwacji z opcją wysyłki do opiekuna\n• Signed URL: 15-minutowy bezpieczny token WebSocket bez ekspozycji API key"
    p_w.font.size = Pt(13)
    p_w.font.color.rgb = WHITE

    add_notes(s8, "W PoC agent działa wyłącznie jako widget webowy; kanał telefoniczny przez SIP Trunk to ścieżka docelowa — ta sama konfiguracja agenta.")

    # ----------------------------------------------------
    # SLIDE 9: Live Demo Paths
    # ----------------------------------------------------
    s9 = prs.slides.add_slide(blank_layout)
    add_bg(s9, CREAM)
    add_header(s9, "Demo: 3 ścieżki walidacji", "LIVE SCENARIOS", dark_theme=False)

    img_succ = os.path.join(assets_dir, 'anna_widget_success.jpg')
    if os.path.exists(img_succ):
        s9.shapes.add_picture(img_succ, Inches(0.8), Inches(1.8), Inches(3.2))

    tb9 = s9.shapes.add_textbox(Inches(4.4), Inches(1.8), Inches(8.1), Inches(5.0))
    tf9 = tb9.text_frame
    tf9.word_wrap = True

    scenarios = [
        ("Ścieżka A: Rezerwacja Zabiegu SPA (Happy Path)", "Gość pyta o masaż leczniczy -> Anna sprawdza kalendarz -> proponuje 14:30 -> parafrazuje dane -> potwierdza rezerwację SPA-4821 -> wysyła SMS."),
        ("Ścieżka B: Zapytanie Informacyjne z RAG", "Pytanie o godziny posiłków dietetycznych i dojazd meleksem -> precyzyjna odpowiedź z bazy wiedzy bez halucynacji."),
        ("Ścieżka C: Eskalacja Medyczna / Przeciwwskazanie", "Gość zgłasza dolegliwości kardiologiczne przy kąpieli siarczkowej -> Anna natychmiast przełącza na dyżurkę medyczną.")
    ]

    for i, (sc_title, sc_desc) in enumerate(scenarios):
        p = tf9.paragraphs[0] if i == 0 else tf9.add_paragraph()
        p.text = f"{sc_title}"
        p.font.size = Pt(15)
        p.font.bold = True
        p.font.color.rgb = NAVY

        p_b = tf9.add_paragraph()
        p_b.text = f"{sc_desc}\n"
        p_b.font.size = Pt(12)
        p_b.font.color.rgb = CHARCOAL

    add_notes(s9, "Miej przygotowany fallback: jeśli internet padnie, pokaż logi z FastAPI lub nagrania audio.")

    # ----------------------------------------------------
    # SLIDE 10: Security & Compliance
    # ----------------------------------------------------
    s10 = prs.slides.add_slide(blank_layout)
    add_bg(s10, NAVY)
    add_header(s10, "Enterprise Ready: RODO i ochrona danych medycznych", "SECURITY & COMPLIANCE", dark_theme=True)

    img_sec = os.path.join(assets_dir, 'enterprise_security.png')
    if os.path.exists(img_sec):
        s10.shapes.add_picture(img_sec, Inches(0.8), Inches(1.8), Inches(6.8))

    tb10 = s10.shapes.add_textbox(Inches(7.9), Inches(1.8), Inches(4.7), Inches(5.0))
    tf10 = tb10.text_frame
    tf10.word_wrap = True

    sec_items = [
        ("Zero Retention Mode (ZRM):", "Audio i transkrypcje przetwarzane wyłącznie w pamięci RAM — brak zapisu na dyskach ElevenLabs."),
        ("Data Redaction:", "Automatyczne maskowanie danych osobowych (PII) i medycznych w logach."),
        ("Data Residency EU:", "Przetwarzanie danych na terenie Unii Europejskiej, pełna zgodność z RODO / DPA."),
        ("Signed URLs:", "Bezpieczne tokeny jednorazowe eliminujące wyciek klucza API do przeglądarki.")
    ]

    for i, (it_title, it_desc) in enumerate(sec_items):
        p = tf10.paragraphs[0] if i == 0 else tf10.add_paragraph()
        p.text = f"🔒 {it_title}"
        p.font.size = Pt(14)
        p.font.bold = True
        p.font.color.rgb = GOLD

        p_b = tf10.add_paragraph()
        p_b.text = f"{it_desc}\n"
        p_b.font.size = Pt(12)
        p_b.font.color.rgb = WHITE

    add_notes(s10, "Dla zarządu sieci hoteli compliance medyczne to warunek sine qua non.")

    # ----------------------------------------------------
    # SLIDE 11: Multi-Hotel Architecture
    # ----------------------------------------------------
    s11 = prs.slides.add_slide(blank_layout)
    add_bg(s11, NAVY)
    add_header(s11, "Jeden agent, dziesięć hoteli — skalowanie sieciowe", "MULTI-TENANT ARCHITECTURE", dark_theme=True)

    img_multi = os.path.join(assets_dir, 'diagram_multihotel.png')
    if os.path.exists(img_multi):
        s11.shapes.add_picture(img_multi, Inches(0.8), Inches(1.8), Inches(6.8))

    tb11 = s11.shapes.add_textbox(Inches(7.9), Inches(1.8), Inches(4.7), Inches(5.0))
    tf11 = tb11.text_frame
    tf11.word_wrap = True

    p = tf11.paragraphs[0]
    p.text = "Architektura Multi-Hotel"
    p.font.size = Pt(18)
    p.font.bold = True
    p.font.color.rgb = GOLD

    p_body = tf11.add_paragraph()
    p_body.text = "• 1 Centralny Agent: Zamiast 10 osobnych botów utrzymujemy jeden rdzeń system promptu.\n\n• Dynamic Variables: Przy inicjacji połączenia wstrzykujemy parametry:\n  - hotel_name, location\n  - reception_phone\n  - pms_hotel_id\n\n• Sygnalizacja SIP UUI: Przekazywanie ID hotelu w nagłówkach centrali PBX.\n\n• Skalowalność: Dodanie 11. obiektu to 5 minut konfiguracji zmiennych."
    p_body.font.size = Pt(12)
    p_body.font.color.rgb = WHITE

    add_notes(s11, "Pokaż, jak myślisz jako Deployment Strategist: optymalizacja kosztów utrzymania i zarządzania agentami.")

    # ----------------------------------------------------
    # SLIDE 12: Costs & ROI
    # ----------------------------------------------------
    s12 = prs.slides.add_slide(blank_layout)
    add_bg(s12, CREAM)
    add_header(s12, "Koszty wdrożenia i twardy zwrot z inwestycji (ROI)", "BUSINESS CASE & FINANCIALS", dark_theme=False)

    # Cost table
    table_shape = s12.shapes.add_table(4, 3, Inches(0.8), Inches(1.9), Inches(11.7), Inches(2.3))
    table = table_shape.table
    table.columns[0].width = Inches(3.9)
    table.columns[1].width = Inches(3.9)
    table.columns[2].width = Inches(3.9)

    c_headers = ["Parametr", "Faza Pilotażu / PoC (Creator)", "Faza Skalowania (Scale)"]
    for idx, h in enumerate(c_headers):
        cell = table.cell(0, idx)
        cell.fill.solid()
        cell.fill.fore_color.rgb = NAVY
        p = cell.text_frame.paragraphs[0]
        p.text = h
        p.font.bold = True
        p.font.color.rgb = GOLD
        p.font.size = Pt(13)

    c_data = [
        ("Koszt platformy", "$22 / miesiąc", "$299 / miesiąc"),
        ("Minuty w pakiecie", "275 minut rozmów", "3 738 minut rozmów"),
        ("Jednoczesne połączenia (Concurrency)", "10 kanałów", "30 kanałów (+Burst do 90)")
    ]

    for row_idx, (c1, c2, c3) in enumerate(c_data, start=1):
        for col_idx, val in enumerate([c1, c2, c3]):
            cell = table.cell(row_idx, col_idx)
            cell.fill.solid()
            cell.fill.fore_color.rgb = WHITE if row_idx % 2 == 1 else RGBColor(250, 246, 240)
            p = cell.text_frame.paragraphs[0]
            p.text = val
            p.font.size = Pt(12)
            p.font.color.rgb = CHARCOAL

    tb12 = s12.shapes.add_textbox(Inches(0.8), Inches(4.5), Inches(11.7), Inches(2.4))
    tf12 = tb12.text_frame
    tf12.word_wrap = True

    p = tf12.paragraphs[0]
    p.text = "Kalkulacja ROI (Return on Investment):"
    p.font.size = Pt(16)
    p.font.bold = True
    p.font.color.rgb = NAVY

    p_roi = tf12.add_paragraph()
    p_roi.text = "• Koszt 275 min AI ($22) odpowiada kosztowi zaledwie 3,5 godziny pracy recepcjonisty (~25 PLN/h).\n• Ochrona Przychodów: Pozyskanie 2 rezerwacji pokoju w nocy (2 x 500 PLN) pokrywa miesięczny abonament Scale.\n• Wartość dla Personelu: Zero wypalenia zawodowego i możliwość skupienia się na gościach obecnych fizycznie w obiekcie."
    p_roi.font.size = Pt(13)
    p_roi.font.color.rgb = CHARCOAL

    add_notes(s12, "Nie pozycjonujemy AI jako redukcji personelu. To ochrona przed utraconym przychodem w nocy i w szczytach.")

    # ----------------------------------------------------
    # SLIDE 13: Roadmap
    # ----------------------------------------------------
    s13 = prs.slides.add_slide(blank_layout)
    add_bg(s13, CREAM)
    add_header(s13, "Roadmapa wdrożenia: od PoC do proaktywnego AI", "IMPLEMENTATION TIMELINE", dark_theme=False)

    phases = [
        ("Faza I: PoC & Walidacja (Obecnie)", "• Baza wiedzy RAG (5 plików)\n• Mock backend (FastAPI, 7 narzędzi webhook)\n• Widget webowy z Quick Reply Chips\n• Testy czasu reakcji i promptu", SAGE),
        ("Faza II: Integracja Produkcyjna (Miesiąc 1-2)", "• Bezpośrednie API do PMS (Opera/KWHotel)\n• Bramka Twilio SMS (potwierdzenia)\n• Wpięcie w centralę telefoniczną SIP PBX\n• Wielojęzyczność (DE, EN, UA)", GOLD),
        ("Faza III: Proaktywny Outbound AI (Miesiąc 3+)", "• Automatyczne telefony przed przyjazdem\n• Potwierdzanie transportu meleksem\n• Spersonalizowane rekomendacje zabiegów\n• Zaawansowana analityka intencji i CSAT", NAVY)
    ]

    for i, (ph_title, ph_desc, col_accent) in enumerate(phases):
        left = Inches(0.8 + i * 4.0)
        box = s13.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, left, Inches(1.9), Inches(3.7), Inches(5.0))
        box.fill.solid()
        box.fill.fore_color.rgb = WHITE
        box.line.color.rgb = col_accent
        box.line.width = Pt(2)

        tb = s13.shapes.add_textbox(left + Inches(0.2), Inches(2.1), Inches(3.3), Inches(4.5))
        tf = tb.text_frame
        tf.word_wrap = True
        p = tf.paragraphs[0]
        p.text = ph_title
        p.font.size = Pt(16)
        p.font.bold = True
        p.font.color.rgb = NAVY

        p_b = tf.add_paragraph()
        p_b.text = f"\n{ph_desc}"
        p_b.font.size = Pt(12)
        p_b.font.color.rgb = CHARCOAL

    add_notes(s13, "Faza III to przejście od reaktywnej infolinii do proaktywnego generatora przychodów.")

    # ----------------------------------------------------
    # SLIDE 14: Q&A
    # ----------------------------------------------------
    s14 = prs.slides.add_slide(blank_layout)
    add_bg(s14, NAVY)

    tb14 = s14.shapes.add_textbox(Inches(1.5), Inches(2.5), Inches(10.3), Inches(3.0))
    tf14 = tb14.text_frame
    tf14.word_wrap = True
    p = tf14.paragraphs[0]
    p.alignment = PP_ALIGN.CENTER
    p.text = "Dziękuję za uwagę."
    p.font.size = Pt(40)
    p.font.bold = True
    p.font.color.rgb = GOLD
    p.font.name = 'Georgia'

    p2 = tf14.add_paragraph()
    p2.alignment = PP_ALIGN.CENTER
    p2.text = "\nCzas na dyskusję, pytania i sesję System Design (V2)."
    p2.font.size = Pt(22)
    p2.font.color.rgb = WHITE

    add_notes(s14, "Otwórz dyskusję i przejdź do warsztatu projektowego.")

    out_path = os.path.join(os.path.dirname(__file__), 'Bukowy_Dwor_Case_Study.pptx')
    prs.save(out_path)
    print("Prezentacja wygenerowana pomyslnie: " + out_path)

if __name__ == '__main__':
    create_presentation()
