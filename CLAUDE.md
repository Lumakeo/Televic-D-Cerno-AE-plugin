# Televic D-Cerno AE Plugin

## GitHub Sync Rules

- **Always keep GitHub in sync.** After every code change in this project, stage, commit, and push all changes to `origin main`.
- The remote repository is: https://github.com/Lumakeo/Televic-D-Cerno-AE-plugin
- GitHub account: Lumakeo
- Use descriptive commit messages that reflect what changed.
- Never leave uncommitted changes at the end of a session.

## Sync workflow (run after every change)

```bash
git add -A
git commit -m "<description of change>"
git push origin main
```

---

## Progetto: Confero Agenda Manager

### Stato attuale (2026-04-21)
Il file principale `Confero-Agenda.qplug` è stato creato e pushato su GitHub (commit `76687cb`).

### Cosa è stato realizzato
Plugin Q-SYS in Lua (~990 righe) per la gestione di ordine del giorno e votazioni su sistemi **Televic Confero (Plixus / G4)**.

**File:**
- `Confero-Agenda.qplug` — plugin principale (unico file Lua, pronto per Q-SYS Designer)
- `Confero_V1.2.0-Beta.qplug` — plugin Beta di riferimento (non modificare, usato solo come fonte di ispirazione)
- `content/` — asset immagine e documentazione originale Televic
- `REST API Confero.txt` — link alla documentazione API v7.17

**Architettura del plugin:**
- 5 tab: Ordine del Giorno, Riunione, Voting, Risultati, Info
- ~180 controlli Q-SYS
- State machine: `NotConnected → MeetingReady → MeetingActive → VotingActive`
- Comunicazione HTTP con API REST Confero v7.17 (porta 9443 HTTPS / 9080 HTTP)
- Auth: `Bearer Token` su ogni richiesta
- JSON via `require("json")` (stessa API del Beta plugin)
- Persistenza dati OdG su file filesystem Q-SYS (agendas.json)
- Poll timer: 5s a riposo, 2s durante votazione

**Pattern HTTP (dal Beta plugin):**
```lua
HttpClient.Download({ Url=..., Method="GET", Headers=..., Timeout=10, VerifyPeer=false, EventHandler=fn })
HttpClient.Upload({   Url=..., Method="POST"/"PUT"/"DELETE", Data=..., Headers=..., EventHandler=fn })
HttpClient.CreateUrl({ Host="https://IP", Port=9443, Path="api/..." })
```

**Endpoint API principali usati:**
| Metodo | Path | Scopo |
|--------|------|-------|
| GET    | `api/meeting` | Verifica riunione attiva, recupera meetingId |
| POST   | `api/meeting` | Avvia riunione `{title, date}` |
| DELETE | `api/meeting` | Termina riunione |
| POST   | `api/meeting/actions` | Azioni: `StartVotingAction`, `StopVotingAction`, `StartDiscussionAction`, `StopDiscussionAction` |
| GET    | `api/meeting/voting-results` | Risultati votazione live |

### Prossimi passi
1. Aprire `Confero-Agenda.qplug` in **Q-SYS Designer** → verifica compilazione design-time
2. Avviare in modalità **emulazione** → verificare rendering 5 tab
3. Test connessione con sistema Confero reale (IP + Bearer Token nelle Properties)
4. Eventuali fix basati sui test (nomi endpoint, formato JSON richieste, codici risposta)
5. Creazione `sample_agenda.json` per test import
