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

### Stato attuale (2026-04-21) — v2.0.0 (commit `b0e55e5`)

Plugin Q-SYS in Lua per gestione ordine del giorno, votazioni, sedili e audio su **Televic Confero (Plixus/G4)**.

**File:**
- `Confero-Agenda.qplug` — plugin principale (~1300 righe)
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
- Persistenza OdG su file (`agendas.json`)
- Data formato italiano: `GG/MM/AAAA`

**4 timer (runtime):**
| Timer | Frequenza | Funzione |
|-------|-----------|----------|
| `PollTimer` | 0.5s | Volume headphone + speaker |
| `SeatTimer` | 0.5s | Stato speaker ai microfoni |
| `MeetingTimer` | 2s | api/meeting + lista richieste + risultati voto |
| `RecordingTimer` | 0.5s | Stato registrazione |

**Avviati da `ConnectServer` (Toggle). Fermati se `ConnectServer` → off.**

**Endpoint API usati:**
| Metodo | Path | Scopo |
|--------|------|-------|
| GET | `api/meeting` | Stato riunione |
| POST/DELETE | `api/meeting` | Avvia/termina riunione |
| POST | `api/meeting/actions` | Start/Stop Voting/Discussion |
| GET | `api/meeting/voting-results` | Risultati live |
| GET/PUT | `api/room/seats/discussion` | Sedili microfono |
| GET | `api/discussion/speakers` | Speaker attivi |
| PUT | `api/discussion/seats/{id}` | Accendi/spegni mic |
| GET | `api/discussion/requests` | Lista richieste parola |
| GET/PUT | `api/audio/loudspeakervolume` | Volume speaker |
| GET/PUT | `api/audio/defaultchannelselectorvolume` | Volume headphone |
| POST | `api/v1/audio/.../apply` (porta 9012) | Applica volume |
| GET/PUT | `api/recording/state` | Stato registrazione |
| GET | `api/device/devices` | Dispositivi wireless |
| POST | `api/device/devices/actions` | Shutdown wireless |

**Pattern HTTP:**
```lua
HttpClient.Download({ Url=BuildUrl(path), Method="GET", Headers=AuthHdrGet(), Timeout=10, VerifyPeer=false, EventHandler=fn })
HttpClient.Upload({   Url=BuildUrl(path), Method="PUT"/"POST"/"DELETE", Data=rj.encode(data), Headers=AuthHdrPost(), ... })
```

### Prossimi passi
1. Aprire in **Q-SYS Designer** → verifica compilazione design-time (0 errori orange)
2. Emulazione → verificare 7 tab e griglia sedili (Seats=12 → 12 pulsanti)
3. Test connessione reale (IP + Bearer Token nelle Properties, ConnectServer ON)
4. Eventuali fix endpoint/JSON basati sui test
