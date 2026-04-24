# Televic D-Cerno AE Plugin

## GitHub Sync Rules

- **Always keep GitHub in sync.** After every code change, stage, commit, and push to `origin main`.
- Remote: https://github.com/Lumakeo/Televic-D-Cerno-AE-plugin — account: Lumakeo
- Use descriptive commit messages. Never leave uncommitted changes at end of session.

```bash
git add -A && git commit -m "<description>" && git push origin main
```

---

## Progetto: Confero Agenda Manager

### Stato attuale (2026-04-24) — v2.2.0 (commit `a272e70`)

Plugin Q-SYS in Lua per gestione ordine del giorno, votazioni, sedili e audio su **Televic Confero (Plixus/G4)**.

**File:**
- `Confero-Agenda.qplug` — plugin principale (~1750 righe)
- `Agenda Builder.html` — tool HTML standalone per creare OdG con config votazioni
- `KeyGen.py` — generatore chiavi di licenza (uso sviluppatore, Python 3.6+)
- `Confero_V1.2.0-Beta.qplug` — riferimento Beta (non modificare)
- `content/` — asset e documentazione Televic
- `REST API Confero.txt` — link API v7.17

**Architettura:**
- **7 tab**: Ordine del Giorno, Riunione, Votazione, Risultati, Sistema/System, Wireless, Info
- **Proprietà**: System Type, Server IP, Use HTTPS, Bearer Token, Data File Path, Seats (1–300), **LicenseKey**
- Tutti i controlli multi-istanza dichiarati individualmente con `nome_N` (underscore, NO Count>1)
- Controlli dinamici: `SeatButton_N` e `RequestLED_N` (loop su `props["Seats"].Value`)
- State machine: `NotConnected → MeetingReady → MeetingActive → VotingActive`
- Auth: `Bearer Token` — JSON via `require("json")`
- Persistenza OdG su file — default `/data/agendas.json` (percorso assoluto Q-SYS)
- Data formato italiano `GG/MM/AAAA` nel display; convertita in `YYYY-MM-DD` per l'API
- Finestra: **1100px** di larghezza

**4 timer (runtime):**
| Timer | Frequenza | Funzione |
|-------|-----------|----------|
| `PollTimer` | 0.5s | Volume headphone + speaker |
| `SeatTimer` | 0.5s | Stato speaker ai microfoni |
| `MeetingTimer` | 2s | api/meeting + lista richieste + risultati voto |
| `RecordingTimer` | 0.5s | Stato registrazione |

**Avviati da `ConnectServer` (Toggle). Fermati se `ConnectServer` → off.**

---

## Sistema di licenza (v2.2.0)

- In **emulazione** (`System.IsEmulating()`): licenza sempre valida, `ConnectServer` abilitato.
- Su **Core fisico**: al boot il plugin esegue `GET https://127.0.0.1/api/v0/cores` (porta 443, no auth), estrae `hardwareId`, calcola la chiave attesa e confronta con `Properties["LicenseKey"].Value`.
- Se la chiave non è valida: `ConnectServer` è disabilitato e il tab Info mostra un avviso.
- Il tab Info espone il **Core Hardware ID** in sola lettura per permettere la richiesta di licenza.

**Algoritmo (deterministico, segreto incorporato):**
```lua
SECRET = "CONFERO_PRASE_MIDWICH_2026"
CHARS  = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"  -- 32 char (no I,O,1,0)
s = hardwareId .. SECRET
h  = hash polinomiale forward  (base 31, MOD 1e9)
h2 = hash polinomiale backward (base 37, peso posizione % 7 + 1, MOD 1e9)
key = enc(h,4) .. "-" .. enc(h2,4) .. "-" .. enc((h+h2)%MOD, 4)
-- enc(n,4): 4 char in base 32 da CHARS
```

**Core fisico noto:**
- IP: `172.16.17.210` — Modello: Core 110f — S/N: `21MX2321200812`
- hardwareId: `3-86AC24DA6D61EEC8D22C9BFA99A9BECD`
- Chiave: **`HYFK-H882-QEUN`**

**Generazione chiave sviluppatore:**
```bash
python KeyGen.py <hardware_id>
```

---

## Comportamento API confermato da test diretti (172.16.17.202)

| Endpoint | Metodo | Note |
|----------|--------|------|
| `api/meeting` | GET | 200 + `{meetingId, title, participants}` se attiva; **412** se nessuna riunione |
| `api/meeting` | POST | Richiede `{title, date(ISO), participants:[...]}`. Risposta: **UUID stringa grezza** (non JSON) = meetingId |
| `api/meeting` | DELETE | 204 |
| `api/meeting/actions` | POST | Vedi sotto |
| `api/meeting/voting-results` | GET | `{votingId, votingTitle, global:[{choiceId,choiceTitle,count}], individual:[]}` |
| `api/room/seats/discussion` | GET | Lista sedili con `{seatNumber, state, units[], capabilities[], role}` |
| `https://127.0.0.1/api/v0/cores` | GET | Info Core (no auth): `{hardwareId, serialNo, model, ...}` — usato per licenza |

**Payload azioni meeting (`POST api/meeting/actions`):**

```lua
-- StartVotingAction
{ kind="StartVotingAction", meetingId=State.meetingId,
  voting={ votingTitle, votingDescription="",
    choices=[{ number, choiceId(str), label, choiceTitle, color, hexColor, button(++/+/0/-/--) }],
    resultVisibility="Public", showResultsRealtime=true } }
-- → risposta: UUID stringa (votingId)

-- StopVotingAction
{ kind="StopVotingAction", meetingId=State.meetingId, votingId=State.votingId }
-- → 204

-- StartDiscussionAction
{ kind="StartDiscussionAction", meetingId=State.meetingId,
  discussion={ title, description="" } }
-- → risposta: UUID stringa (discussionId)

-- StopDiscussionAction
{ kind="StopDiscussionAction", meetingId=State.meetingId, discussionId=State.discussionId }
-- → 204
```

**Struttura State (runtime):**
```lua
State = { current, meetingId, votingId, discussionId, currentItemIdx,
          votingActive, discussionActive, httpErrCount }
```

---

## Cronologia versioni

| Versione | Commit | Novità / Fix |
|----------|--------|--------------|
| v2.0.1 | `efdba05` | `ConvertDateForAPI()` DD/MM→ISO; file path `/data/agendas.json`; volume text `.String`; guard OdG vuoto |
| v2.0.2 | `6145d10` | `POST api/meeting` richiede `participants:[]`; risposta UUID grezzo; `StartVotingAction` richiede `choiceId`, `choiceTitle`, `hexColor`, `button`; `StopVoting` richiede `votingId`; `StopDiscussion` richiede `discussionId`; risultati voto usano campo `global` con `choiceTitle` |
| v2.0.3 | `b9db6fe` | `StartMeeting` auto-popola `participants` da `GET api/room/seats/discussion`; fallback a `participants:[]` se 500 — **rollback in v2.0.4** |
| v2.0.4 | `bdfd6aa` | Revert `StartMeeting` a `participants:[]` diretto — server restituisce 400 (non 500) per qualsiasi struttura participant; il fallback v2.0.3 non scattava |
| v2.0.5 | `25c8cb0` | `OnGetVotingResults`: 412/404 silenzioso (reset `votingActive`, transizione a MeetingActive); ignora 500 transitorio post-avvio; `OnEndMeeting` resetta `votingActive`+`discussionActive` |
| v2.0.6 | `6d71c79` | `StartMeeting` popola `participants` con `presence:{kind="LocalParticipantPresence",seatNumber=N}` — attiva LED F-DV durante votazione; fallback a `participants:[]` se server rifiuta |
| v2.1.0 | `a3a5800` | UI overhaul: finestra 1100px; barra connessione compatta su tutti i 7 tab; max scelte votazione ridotto a 5 (da 6, per hardware F-DV); `Agenda Builder.html` standalone |
| v2.2.0 | `a272e70` | Sistema licenza: `CheckLicense()` via `GET https://127.0.0.1/api/v0/cores`; hash polinomiale `computeLicenseKey()`; bypass in emulazione; tab Info mostra Core Hardware ID e stato; `KeyGen.py` |

---

## Note critiche Q-SYS

- `Count>1` nei controlli genera nomi con spazio (`"nome 1"`) → sempre `nil` a runtime. Usare loop con `nome_N`.
- `.Choices={val}` ignorato su `Style="Text"` → usare `.String=tostring(val)`.
- `io.open` con path relativo fallisce → usare percorso assoluto (es. `/data/agendas.json`).
- Risposte API UUID sono stringhe grezze (non JSON) → parsare con `data:match("^%s*(.-)%s*$")`.
- `GET api/meeting` → 412 quando nessuna riunione attiva (gestito come 404).
- `HttpClient.Download` accetta URL da `HttpClient.CreateUrl({Host, Port, Path})`.

## Note critiche Confidea F-DV

- Il campo `button` in ogni choice (`++/+/0/-/--`) mappa ai 5 tasti fisici del dispositivo.
- Con 3 scelte (Sì/No/Astenuto): tasti `+`, `-`, `0` accesi; `++` e `--` restano spenti (corretto).
- I LED F-DV si attivano **solo se il sedile è in `participants`** con `presence.kind="LocalParticipantPresence"`.
- Struttura participant corretta: `{participantId, firstName, lastName, presence:{kind="LocalParticipantPresence", seatNumber=N}}`
- `POST api/meeting` con struttura sbagliata (senza `kind`) → 400 "Invalid ParticipantPresence".
- Valori `kind` accettati: `LocalParticipantPresence`, `RemoteParticipantPresence`, `AbsentParticipantPresence`.
- `PATCH api/room/seats/voting` → 400 "Missing json field: role" (formato ancora non decifrabile).
- **LED sempre blu**: la Confidea F-DV usa blu fisso indipendentemente da `color`/`hexColor` nel payload — è il colore hardware del firmware Plixus. `color`/`hexColor` servono solo per display software. Blu lampeggiante/fisso = votazione aperta; blu fisso sul tasto premuto = voto registrato.

## Note critiche sistema di licenza

- `System.IsEmulating()` è sincrono — verificare sempre prima di fare HTTP a localhost.
- `GET https://127.0.0.1/api/v0/cores` non richiede autenticazione; VerifyPeer=false.
- Il SECRET `"CONFERO_PRASE_MIDWICH_2026"` è incorporato nel plugin — non modificarlo tra versioni senza rigenerare tutte le chiavi esistenti.
- Il campo è `hardwareId` (camelCase) nella risposta JSON del Core.

### Prossimi passi
1. Test hardware v2.2.0: caricare su Core 110f (172.16.17.210), verificare che CheckLicense legga correttamente l'hardwareId e accetti la chiave `HYFK-H882-QEUN`
2. Verificare percorso file OdG scrivibile sul Q-Core hardware (es. `/tmp/agendas.json`)
