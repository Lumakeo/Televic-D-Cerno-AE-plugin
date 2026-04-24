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

### Stato attuale (2026-04-24) — v2.2.6

Plugin Q-SYS in Lua per gestione ordine del giorno, votazioni, sedili e audio su **Televic Confero (Plixus/G4)**.

**File:**
- `Confero-Agenda.qplug` — plugin principale (~1800 righe)
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
- Persistenza OdG su file — default `media/Televic Meeting/agendas.json` (percorso relativo Q-SYS, cartella media)
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
| v2.2.1 | `ec571a4` | Fix loop runtime non allineati ai controlli v2.1.0: `for m=1,6→1,5` su choice/result controls; `for i=1,4→1,3` su vote_mode buttons — causava nil index crash al boot |
| v2.2.2 | `54b0ae0` | `CheckLicense`: usa `System.SerialNumber` (nativo Lua) prima di HTTP; fallback HTTP porta 80 (non 443); `System.IsEmulating` senza parentesi (è proprietà, non funzione) |
| v2.2.3 | `7693e1d` | `OnStartVoting` azzera `vote_result_*` e chiama `RefreshVotingPanel()` alla partenza; log diagnostico VoteResults; note: API Plixus non espone conteggi live (tot=0 durante votazione) |
| v2.2.4 | `ba54a42` | Fix race condition polling: `votingStartTime` + grace period 3s per 412; `votingActive=true` impostato DOPO `TransitionTo`; `OnStopVoting` cattura `closedVotingId`; `MeetingTimer` polla anche su `State.current=="VotingActive"`; pre-popola label risultato da choice label |
| v2.2.5 | `51a11ac` | Fix path file OdG: default `media/agendas.json` (era `/data/agendas.json`); aggiunto folder scanner nel Tab 1: `Cerca file JSON` scansiona la cartella e lista i `.json` disponibili; `Carica selezionato` carica l'OdG dal file scelto |
| v2.2.6 | — | Fix `Status` ("OK") posizionato in header (y=8) → spostato nella connbar (y=44); default path → `media/Televic Meeting/agendas.json`; `SaveToFile` tenta `lfs.mkdir` sulla directory prima di scrivere |

---

## Note critiche Q-SYS

- `Count>1` nei controlli genera nomi con spazio (`"nome 1"`) → sempre `nil` a runtime. Usare loop con `nome_N`.
- `.Choices={val}` ignorato su `Style="Text"` → usare `.String=tostring(val)`.
- `io.open` usa percorsi relativi con prefisso `media/` (es. `media/agendas.json`). Percorsi assoluti tipo `/data/agendas.json` non funzionano sul Core.
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

- `System.IsEmulating` (senza parentesi) è una proprietà booleana Lua nativa Q-SYS.
- `CheckLicense` tenta prima `System.SerialNumber` (proprietà Lua, no HTTP); fallback a `GET http://127.0.0.1:80/api/v0/cores` (HTTP porta 80, non HTTPS 443).
- Il SECRET `"CONFERO_PRASE_MIDWICH_2026"` è incorporato nel plugin — non modificarlo tra versioni senza rigenerare tutte le chiavi esistenti.
- La risposta JSON di `api/v0/cores` ha campo `hardwareId` (camelCase); `serial`/`naturalId` hanno lo stesso valore.
- Chiave per Core 110f (`hardwareId=3-86AC24DA6D61EEC8D22C9BFA99A9BECD`): **`HYFK-H882-QEUN`** ✓ verificata.

## Note critiche votazione (comportamento API Plixus confermato)

- `GET api/meeting/voting-results` restituisce **sempre `count=0`** durante votazione attiva — il server Plixus accumula i voti internamente e li espone solo dopo la chiusura (`StopVotingAction`). I risultati live nel plugin non sono possibili.
- Race condition risolta in v2.2.4: `votingActive=true` impostato DOPO `TransitionTo("VotingActive")`; grace period 3s per 412; `OnStopVoting` usa `closedVotingId` per non killare votazione successiva.
- `resultVisibility="Individual"`: controlla cosa vedono i **partecipanti** sul proprio dispositivo F-DV (solo il proprio voto, non il totale). Il plugin operatore vede sempre i risultati globali — comportamento corretto.

## Note file OdG

- Percorso default `media/agendas.json` — relativo alla cartella media Q-SYS. Modificabile nelle Properties.
- "Genera Export" → JSON nel campo testo (copia/incolla). "Salva" → scrive su file nel Core.
- "Cerca file JSON" (Tab 1, in basso) → scansiona la cartella del file configurato e lista tutti i `.json` disponibili. "Carica selezionato" → carica il file scelto.

### Prossimi passi
1. Testare risultati post-votazione: dopo chiusura i conteggi finali devono apparire correttamente
