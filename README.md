# Confero Agenda Manager — Plugin Q-SYS

Plugin Q-SYS in Lua per la gestione di ordine del giorno, votazioni, sedili e audio su sistemi **Televic Confero (Plixus / G4)**.

**Versione attuale: 2.2.0**
Autore: Matteo Fioretto — Prase, a Midwich company

---

## File inclusi

| File | Descrizione |
|------|-------------|
| `Confero-Agenda.qplug` | Plugin principale da importare in Q-SYS Designer |
| `Agenda Builder.html` | Tool web standalone per creare ordini del giorno con config votazioni |
| `KeyGen.py` | Script Python per generare chiavi di licenza (uso sviluppatore) |

---

## Installazione del plugin

1. Aprire **Q-SYS Designer**.
2. Dal menu *File → Import Plugin*, selezionare `Confero-Agenda.qplug`.
3. Trascinare il blocco **Confero Agenda Manager** nel design.
4. Configurare le proprietà (vedi sezione successiva).
5. Salvare e distribuire il design sul Core.

---

## Proprietà del plugin

| Proprietà | Tipo | Descrizione |
|-----------|------|-------------|
| System Type | Enum | `Plixus` o `G4` |
| Server IP | String | IP del server Confero (es. `172.16.17.202`) |
| Use HTTPS | Boolean | Attiva HTTPS (porta 9443); disattivo = HTTP (porta 9080) |
| Bearer Token | String | Token di autenticazione API Confero |
| Data File Path | String | Percorso assoluto per il salvataggio OdG (default `/data/agendas.json`) |
| Seats | Integer (1–300) | Numero di sedili/basi da gestire |
| LicenseKey | String | Chiave di licenza (formato `XXXX-XXXX-XXXX`) |

---

## Licenza

Il plugin richiede una chiave di licenza univoca per ogni Core Q-SYS quando viene eseguito su hardware reale. In **modalità emulazione** (Q-SYS Designer) la licenza non è richiesta.

### Come ottenere la chiave

1. Caricare il design sul Core fisico.
2. Aprire il tab **Info** del plugin: il campo **Core Hardware ID** mostra l'ID dell'hardware.
3. Comunicare l'ID a Prase/Midwich per ricevere la chiave.
4. Incollare la chiave nella proprietà **LicenseKey** e ridistribuire il design.

### Generazione chiave (sviluppatore)

```bash
python KeyGen.py <hardware_id>
# Esempio:
python KeyGen.py 3-86AC24DA6D61EEC8D22C9BFA99A9BECD
# Output: HYFK-H882-QEUN
```

Richiede Python 3.6+. Nessuna dipendenza esterna.

---

## Agenda Builder (tool web)

`Agenda Builder.html` è un'applicazione HTML standalone (nessuna installazione richiesta) per comporre ordini del giorno con configurazione votazioni.

**Utilizzo:**
1. Aprire il file `Agenda Builder.html` in qualsiasi browser moderno.
2. Inserire titolo e data della riunione.
3. Aggiungere i punti dell'ordine del giorno con il pulsante **+ Aggiungi punto**.
4. Per ogni punto con votazione: attivare il toggle votazione, scegliere il numero di scelte (2–5), inserire etichette e colori HEX, configurare visibilità e realtime.
5. Cliccare **Copia JSON** per copiare il JSON negli appunti.
6. Nel plugin, tab **Ordine del Giorno**, incollare il JSON nel campo *Import JSON* e cliccare **Importa**.

---

## Interfaccia del plugin

### Tab 1 — Ordine del Giorno
- Crea, salva e carica ordini del giorno con fino a N punti
- Gestione paginata (5 punti per pagina)
- Configurazione votazione per punto: titolo, scelte (max 5), colori, visibilità risultati
- Esporta/importa JSON per lo scambio con Agenda Builder

### Tab 2 — Riunione
- Avvia / termina la riunione (POST/DELETE `api/meeting`)
- Navigazione tra i punti dell'OdG durante la riunione
- Avvia / ferma la discussione sul punto corrente

### Tab 3 — Votazione
- Avvia / ferma la votazione (con o senza configurazione OdG)
- Modalità manuale: titolo e scelte libere
- Visibilità risultati: Pubblica / Individuale; aggiornamento realtime

### Tab 4 — Risultati
- Storico votazioni della sessione (barre progresso + percentuali)
- Paginazione 20 voci per pagina

### Tab 5 — Sistema
- Controllo volume headphone e speaker
- Lista sedili, speaker attivi, richieste di parola
- Controllo registrazione

### Tab 6 — Wireless
- Lista e stato unità wireless
- Shutdown unità wireless

### Tab 7 — Info
- Versione plugin e informazioni
- **Core Hardware ID** (per richiesta licenza)
- **Stato licenza**

---

## Dispositivi fisici supportati

| Dispositivo | Note |
|-------------|------|
| Confidea F-DV | 5 tasti fisici (++/+/0/-/--), LED blu hardware-fixed |
| Microfoni Plixus | Controllo on/off, richiesta di parola |
| Unità wireless G4 | Shutdown remoto |

**Nota LED Confidea F-DV:** il dispositivo usa LED blu indipendentemente dai colori configurati nelle scelte (`color`/`hexColor` servono solo ai display software). LED blu fisso lampeggiante = votazione aperta; LED blu fisso sul tasto premuto = voto registrato.

---

## Requisiti

- Q-SYS Designer 9.x o superiore
- Core Q-SYS compatibile
- Server Televic Confero (Plixus/G4) con API REST v7.17
- Bearer Token valido per l'autenticazione API
- Python 3.6+ (solo per KeyGen.py, uso sviluppatore)

---

## Cronologia versioni

| Versione | Principali novità |
|----------|------------------|
| v2.2.0 | Sistema di licenza basato su hardware ID del Core; KeyGen.py |
| v2.1.0 | UI overhaul: finestra 1100px, barra connessione su tutti i tab, max 5 scelte F-DV; Agenda Builder HTML |
| v2.0.6 | Attivazione LED F-DV con `LocalParticipantPresence` nei participants |
| v2.0.5 | Fix spam log 412 GetVotingResults; reset stato votazione a fine riunione |
| v2.0.4 | Revert participants vuoti (server rifiuta qualsiasi struttura) |
| v2.0.3 | Auto-popola participants da sedili online (rollback in v2.0.4) |
| v2.0.2 | Fix payload voting/discussion actions; campi choiceId, hexColor, button |
| v2.0.1 | Fix formato data API (ISO 8601); percorso file assoluto; volume text |
| v2.0.0 | Prima versione con OdG, votazioni, sedili, audio |
