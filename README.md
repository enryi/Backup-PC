# Sistema di Backup ZIP Progressivo

Un sistema di backup automatico che crea archivi ZIP compressi delle tue cartelle importanti con feedback visivo in tempo reale e logging dettagliato.

## 🚀 Caratteristiche Principali

- **Backup progressivo**: Visualizzazione in tempo reale del progresso con barre di caricamento
- **Massima compressione**: Utilizza ZIP_DEFLATED livello 9 per ottimizzare lo spazio
- **Gestione automatica**: Mantiene automaticamente solo gli ultimi 3 backup e log
- **Logging completo**: Registra tutte le operazioni per troubleshooting
- **Gestione duplicati**: Evita la copia di file già processati
- **Interfaccia colorata**: Output console con Rich per una migliore esperienza utente

## 📁 Struttura del Progetto

```
backup-system/
├── backup.py          # Script principale (deprecato)
├── main.py            # Nuovo entry point principale
├── utils.py           # Logica di backup e utilities
├── src/
│   ├── backup.py      # Modulo backup (se presente)
│   └── utils.py       # Utilities (importate dal main)
├── .env               # Variabili di configurazione
└── README.md          # Questo file
```

## ⚙️ Configurazione

### 1. Installazione Dipendenze

```bash
pip install python-dotenv rich
```

### 2. File di Configurazione (.env)

Crea un file `.env` nella root del progetto:

```env
FOLDER_PATHS=C:\Users\Username\Documents,C:\Users\Username\Desktop,C:\Users\Username\Pictures
SAVE_PATH=D:\Backup
```

**Parametri:**
- `FOLDER_PATHS`: Lista di cartelle da includere nel backup, separate da virgole
- `SAVE_PATH`: Cartella di destinazione dove salvare i backup

### 3. Struttura Cartelle

Il sistema creerà automaticamente la cartella di destinazione se non esiste.

## 🎯 Utilizzo

### Metodo 1: Tramite main.py (Raccomandato)
```bash
python main.py
```

### Metodo 2: Tramite backup.py
```bash
python backup.py
```

### Metodo 3: Utilizzo diretto della funzione
```python
from src.utils import backup_folders

folders = [
    r"C:\Users\Username\Documents",
    r"C:\Users\Username\Desktop"
]
destination = r"D:\Backup"

backup_folders(folders, destination)
```

## 📊 Output del Sistema

### Console Output
- **Progress Bar**: Mostra il progresso globale con file corrente e cartella
- **File Status**: Ogni file viene mostrato come aggiunto, saltato o errore
- **Statistiche**: Conteggio file, durata, dimensione finale e rapporto di compressione

### Esempio Output:
```
[12:34:56] ✓ Aggiunto: Documents\file.txt
[12:34:57] ✓ Aggiunto: Documents\subfolder\image.jpg
Backup progressivo... ████████████████ 45/120 • image.jpg (23/67) • Documents
```

## 📝 Sistema di Logging

### File di Log
Ogni backup genera un log dettagliato salvato come `backup_YYYY-MM-DD_HH-MM-SS.log`

### Informazioni Registrate:
- Timestamp di inizio e fine backup
- Lista completa dei file processati
- Errori e warning dettagliati
- Statistiche finali di compressione
- Informazioni sulle cartelle processate

## 🛡️ Gestione Errori e Sicurezza

### File Saltati Automaticamente:
- `desktop.ini` (file di sistema Windows)
- File già processati (controllo duplicati)
- File non accessibili o danneggiati

### Gestione Errori:
- **File non accessibili**: Vengono saltati con messaggio di errore
- **Cartelle inesistenti**: Vengono ignorate con warning
- **Errori di compressione**: Il processo continua con gli altri file

## 💾 Gestione Spazio e Performance

### Ottimizzazioni:
- **Compressione massima**: ZIP_DEFLATED livello 9
- **Flush periodici**: Ogni 50 file i dati vengono scritti su disco
- **Cleanup automatico**: Mantiene solo gli ultimi 3 backup e log

### Rapporto di Compressione:
Il sistema calcola e mostra automaticamente la percentuale di compressione ottenuta.

## 🔧 Personalizzazione

### Modificare il Numero di Backup Mantenuti:
Nel file `utils.py`, modifica il parametro `max_files` in:
```python
cleanup_old_files(save_path, "backup_*.zip", max_files=5)  # Mantiene 5 backup
```

### Modificare la Frequenza di Flush:
Cambia il numero in:
```python
if total_files_added % 100 == 0:  # Flush ogni 100 file invece di 50
```

## 📋 Requisiti di Sistema

- **Python**: 3.6 o superiore
- **Sistema Operativo**: Windows, macOS, Linux
- **Spazio Disco**: Sufficiente spazio nella cartella di destinazione
- **Permessi**: Accesso in lettura alle cartelle sorgente e scrittura alla destinazione

## 🐛 Troubleshooting

### Problemi Comuni:

**"Nessuna cartella valida trovata!"**
- Verifica che i percorsi nel file `.env` siano corretti
- Controlla che le cartelle esistano e siano accessibili

**Errori di permessi**
- Esegui come amministratore se necessario
- Verifica i permessi sulle cartelle sorgente e destinazione

**File non trovati**
- Alcuni file potrebbero essere in uso da altri programmi
- Il sistema li salterà automaticamente e continuerà

### Log di Debug:
Consulta sempre i file `.log` generati per informazioni dettagliate su errori e operazioni.

## 🔄 Automazione

### Task Scheduler (Windows):
Crea un task programmato per eseguire backup automatici:
```batch
cd /d "C:\path\to\backup-system"
python main.py
```

### Cron (Linux/macOS):
```bash
0 2 * * * cd /path/to/backup-system && python main.py
```

## 📈 Metriche e Statistiche

Al termine di ogni backup, il sistema fornisce:
- Numero totale di file processati
- Tempo di elaborazione
- Dimensione finale dell'archivio
- Percentuale di compressione ottenuta
- Percorso dell'archivio creato

---

**Nota**: Questo sistema è progettato per essere robusto e affidabile, gestendo automaticamente la maggior parte degli errori comuni e fornendo feedback dettagliato su tutte le operazioni.