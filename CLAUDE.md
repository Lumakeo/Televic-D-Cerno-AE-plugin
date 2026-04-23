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

### Stato attuale (2026-04-23) — v2.0.3 (commit `b9db6fe`)

Plugin Q-SYS in Lua per gestione ordine del giorno, votazioni, sedili e audio su **Televic Confero (Plixus/G4)**.

**File:**
- `Confero-Agenda.qplug` — plugin principale (~1350 righe)
- `Confero_V1.2.0-Beta.qplug` — riferimento Beta (non modificare)
- `content/` — asset e documentazione Televic
- `REST API Confero.txt` — link API v7.17

**Architettura:**
- **7 tab**: Ordine del Giorno, Riunione, Votazione, Risultati, Sistema/System, Wireless, Info
- **Proprietà**: System Type, Server IP, Use HTTPS, Bearer Token, Data File Path, **Seats** (1–300)
- Tutti i controlli multi-istanza dichiarati individualmente con `nome_N` (underscore, NO Count>1)
- Controlli dinamici: `SeatButton_N` e `RequestLED_N` (loop su `props["Seats"].Value`)
- State machine: `NotConnected → MeetingReady → MeetingActive → VotingActive`
- Auth: `Bearer Token` — JSON via `require("json")`
- Persistenza OdG su file — default `/data/agendas.json` (percorso assoluto Q-SYS)
- Data formato italiano `GG/MM/AAAA` nel display; convertita in `YYYY-MM-DD` per l'API

**4 timer (runtime):**
| Timer | Frequenza | Funzione |
|-------|-----------|----------|
| `PollTimer` | 0.5s | Volume headphone + speaker |
| `SeatTimer` | 0.5s | Stato speaker ai microfoni |
| `MeetingTimer` | 2s | api/meeting + lista richieste + risultati voto |
| `RecordingTimer` | 0.5s | Stato registrazione |

**Avviati da `ConnectServer` (Toggle). Fermati se `ConnectServer` → off.**

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

## Cronologia fix (da v2.0.0)

| Versione | Commit | Fix |
|----------|--------|-----|
| v2.0.1 | `efdba05` | `ConvertDateForAPI()` DD/MM→ISO; file path `/data/agendas.json`; volume text `.String`; guard OdG vuoto |
| v2.0.2 | `6145d10` | `POST api/meeting` richiede `participants:[]`; risposta è UUID grezzo; `StartVotingAction` richiede `choiceId`, `choiceTitle`, `hexColor`, `button`; `StopVoting` richiede `votingId`; `StopDiscussion` richiede `discussionId`; risultati voto usano campo `global` con `choiceTitle` |
| v2.0.3 | `b9db6fe` | `StartMeeting` auto-popola `participants` da `GET api/room/seats/discussion` (sedili online); fallback a `participants:[]` se server risponde 500 |

---

## Note critiche Q-SYS

- `Count>1` nei controlli genera nomi con spazio (`"nome 1"`) → sempre `nil` a runtime. Usare loop con `nome_N`.
- `.Choices={val}` ignorato su `Style="Text"` → usare `.String=tostring(val)`.
- `io.open` con path relativo fallisce → usare percorso assoluto (es. `/data/agendas.json`).
- Risposte API UUID sono stringhe grezze (non JSON) → parsare con `data:match("^%s*(.-)%s*$")`.
- `GET api/meeting` → 412 quando nessuna riunione attiva (gestito come 404).

## Note critiche Confidea F-DV

- Il campo `button` in ogni choice (`++/+/0/-/--`) mappa ai 5 tasti fisici del dispositivo.
- Con 3 scelte (Sì/No/Astenuto): tasti `+`, `-`, `0` accesi; `++` e `--` restano spenti (corretto).
- I tasti si attivano solo se il sedile è presente nella lista `participants` della riunione.
- `PATCH api/room/seats/voting` esiste (formato non documentato/non decifrabile).

### Prossimi passi
1. Test hardware v2.0.3: verificare che F-DV mostri i LED durante la votazione
2. Se log mostra "retry senza participants": struttura participants non accettata → problema di configurazione hardware
3. Verificare percorso file OdG: impostare `Data File Path` a un percorso scrivibile nel Q-Core
