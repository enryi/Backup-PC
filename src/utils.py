import os
import zipfile
import shutil
from datetime import datetime
import glob
from rich.progress import Progress, BarColumn, TextColumn, TimeRemainingColumn, TaskProgressColumn
from rich.console import Console
import sys
from io import StringIO
import tempfile
import zlib

def readable_folder_name(folder):
    return os.path.basename(os.path.normpath(folder))

def get_current_time():
    return datetime.now().strftime("[%H:%M:%S]")

def cleanup_old_files(save_path, pattern, max_files=3):
    """Rimuove i file più vecchi mantenendo solo max_files"""
    existing_files = sorted(
        glob.glob(os.path.join(save_path, pattern)),
        key=os.path.getctime
    )
    while len(existing_files) >= max_files:
        os.remove(existing_files[0])
        existing_files.pop(0)

def create_progressive_zip_archive(archive_path, folder_paths, console, log_console):
    """Crea un archivio ZIP progressivamente durante la scansione delle cartelle"""
    
    # Configurazione per massima compressione ZIP
    compression_method = zipfile.ZIP_DEFLATED
    compression_level = 9  # Massima compressione (equivalente a -mx=9 in 7-Zip)
    
    console.print(f"[yellow]Creazione archivio ZIP con massima compressione (livello 9)...[/yellow]")
    log_console.print(f"ZIP: Usando compressione {compression_method} livello {compression_level}")
    
    copied_files = set()
    total_files_added = 0
    
    try:
        with zipfile.ZipFile(archive_path, 'w', compression=compression_method, compresslevel=compression_level) as zipf:
            
            # Prima passiamo attraverso tutte le cartelle per contare i file totali
            console.print("[cyan]Conteggio file totali...[/cyan]")
            total_files = 0
            folder_file_counts = {}
            
            for folder in folder_paths:
                folder = folder.strip().strip('"')
                if os.path.exists(folder):
                    folder_name = readable_folder_name(folder)
                    file_count = sum(len(files) for _, _, files in os.walk(folder))
                    folder_file_counts[folder] = file_count
                    total_files += file_count
                    console.print(f"[dim cyan]  {folder_name}: {file_count} file[/dim cyan]")
            
            log_console.print(f"TOTAL FILES TO PROCESS: {total_files}")
            
            # Progress bar globale per tutti i file - fissa in basso
            with Progress(
                TextColumn("[progress.description]{task.description}"),
                BarColumn(),
                TaskProgressColumn(),
                TextColumn("•"),
                TextColumn("[cyan]{task.fields[current_file]}"),
                TextColumn("•"),
                TextColumn("[magenta]{task.fields[current_folder]}"),
                TimeRemainingColumn(),
                console=console,
                transient=True  # La barra rimane fissa
            ) as progress:
                
                main_task = progress.add_task(
                    "Backup progressivo...", 
                    total=total_files,
                    current_file="Inizializzazione...",
                    current_folder=""
                )
                
                # Processa ogni cartella
                for folder in folder_paths:
                    folder = folder.strip().strip('"')
                    if not os.path.exists(folder):
                        error_message = f"ATTENZIONE: La cartella {folder} non esiste!"
                        console.print(f"[red]{error_message}[/red]")
                        log_console.print(f"WARNING: {error_message}")
                        continue
                    
                    folder_name = readable_folder_name(folder)
                    folder_files = folder_file_counts[folder]
                    folder_files_processed = 0
                    
                    progress.update(main_task, current_folder=folder_name)
                    
                    folder_start_message = f"Processando cartella: {folder_name} ({folder_files} file)"
                    console.print(f"[bold cyan]{folder_start_message}[/bold cyan]")
                    log_console.print(f"FOLDER START: {folder_start_message}")
                    
                    # Scansiona e aggiungi file progressivamente
                    for root, dirs, files in os.walk(folder):
                        for file in files:
                            file_path = os.path.join(root, file)
                            folder_files_processed += 1
                            
                            # Salta desktop.ini
                            if file.lower() == "desktop.ini":
                                console.print(f"[dim yellow]{get_current_time()} Saltato: desktop.ini[/dim yellow]")
                                progress.advance(main_task, 1)
                                continue
                            
                            # Controlla duplicati
                            if file_path in copied_files:
                                skip_message = f"File già elaborato: {file}"
                                console.print(f"[dim yellow]{get_current_time()} Saltato: {skip_message}[/dim yellow]")
                                log_console.print(f"SKIP: {skip_message}")
                                progress.advance(main_task, 1)
                                continue
                            
                            # Calcola il nome nell'archivio
                            arcname = os.path.join(folder_name, os.path.relpath(file_path, folder))
                            
                            # Aggiorna display con nome file limitato
                            display_file = file
                            if len(display_file) > 40:
                                display_file = "..." + display_file[-37:]
                            
                            progress.update(
                                main_task, 
                                current_file=f"{display_file} ({folder_files_processed}/{folder_files})",
                                current_folder=folder_name
                            )
                            
                            try:
                                # Verifica accessibilità del file
                                if not (os.path.exists(file_path) and os.access(file_path, os.R_OK)):
                                    error_message = f"File non accessibile: {file_path}"
                                    console.print(f"[red]{get_current_time()} ERRORE: {error_message}[/red]")
                                    log_console.print(f"ERROR: {error_message}")
                                    progress.advance(main_task, 1)
                                    continue
                                
                                # Aggiungi il file all'archivio ZIP
                                zipf.write(file_path, arcname)
                                copied_files.add(file_path)
                                total_files_added += 1
                                
                                # Mostra il file aggiunto sopra la barra
                                console.print(f"[green]{get_current_time()} ✓ Aggiunto: {arcname}[/green]")
                                
                                # Log successo
                                success_message = f"Aggiunto: {arcname}"
                                log_console.print(f"ADDED: {get_current_time()} {success_message}")
                                
                                # Ogni 50 file, forza il flush dei dati
                                if total_files_added % 50 == 0:
                                    # Forza la scrittura dei dati compressi su disco
                                    zipf.fp.flush()  # Flush del buffer del file
                                    os.fsync(zipf.fp.fileno())  # Forza la scrittura su disco
                                    console.print(f"[blue]{get_current_time()} 💾 Flush dati su disco ({total_files_added} file)[/blue]")
                                    log_console.print(f"FLUSH: Forzata scrittura dopo {total_files_added} file")
                                
                            except Exception as e:
                                error_message = f"Errore con {file_path}: {str(e)}"
                                console.print(f"[red]{get_current_time()} ERRORE: {error_message}[/red]")
                                log_console.print(f"ERROR: {error_message}")
                            
                            # Avanza la barra di progresso
                            progress.advance(main_task, 1)
                    
                    folder_complete_message = f"Completata cartella: {folder_name} ({folder_files_processed} file processati)"
                    console.print(f"[bold green]{folder_complete_message}[/bold green]")
                    log_console.print(f"FOLDER COMPLETE: {folder_complete_message}")
                
                # Completa la progress bar
                progress.update(main_task, current_file="Finalizzazione archivio...", current_folder="")
                
        console.print(f"[green]✅ Archivio ZIP creato con successo![/green]")
        log_console.print(f"ZIP SUCCESS: Archivio creato con {total_files_added} file")
        
        return total_files_added
        
    except Exception as e:
        error_msg = f"Errore nella creazione dell'archivio ZIP: {str(e)}"
        console.print(f"[red]{error_msg}[/red]")
        log_console.print(f"ZIP ERROR: {error_msg}")
        raise Exception(error_msg)

def backup_folders(folder_paths, save_path):
    now = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    archive_path = os.path.join(save_path, f"backup_{now}.zip")
    log_path = os.path.join(save_path, f"backup_{now}.log")
    
    # Pulisce i backup vecchi (mantiene gli ultimi 2, più quello corrente = 3 totali)
    cleanup_old_files(save_path, "backup_*.zip", max_files=3)
    
    # Pulisce i log vecchi (mantiene gli ultimi 2, più quello corrente = 3 totali)
    cleanup_old_files(save_path, "backup_*.log", max_files=3)

    # Configurazione console con cattura dell'output
    console = Console()
    log_buffer = StringIO()
    log_console = Console(file=log_buffer, width=120)
    
    # Log di inizio backup
    start_time = datetime.now()
    start_message = f"=== BACKUP INIZIATO (FORMATO ZIP PROGRESSIVO) - {start_time.strftime('%Y-%m-%d %H:%M:%S')} ==="
    console.print(f"[bold yellow]{start_message}[/bold yellow]")
    log_console.print(start_message)
    
    # Informazioni sulla compressione
    compression_info = f"Compressione: ZIP_DEFLATED livello 9 (massima qualità senza perdite)"
    console.print(f"[green]{compression_info}[/green]")
    log_console.print(f"COMPRESSION: {compression_info}")
    
    # Verifica che almeno una cartella esista
    valid_folders = [f.strip().strip('"') for f in folder_paths if os.path.exists(f.strip().strip('"'))]
    if not valid_folders:
        error_msg = "Nessuna cartella valida trovata!"
        console.print(f"[red]{error_msg}[/red]")
        log_console.print(f"FATAL ERROR: {error_msg}")
        return
    
    console.print(f"[cyan]Cartelle da processare: {len(valid_folders)}[/cyan]")
    for folder in valid_folders:
        console.print(f"[dim cyan]  - {readable_folder_name(folder)} ({folder})[/dim cyan]")
    
    try:
        # Creazione progressiva dell'archivio
        console.rule("[bold blue]CREAZIONE ARCHIVIO ZIP PROGRESSIVO")
        log_console.rule("CREAZIONE ARCHIVIO ZIP PROGRESSIVO")
        
        total_files_copied = create_progressive_zip_archive(archive_path, valid_folders, console, log_console)
        
    except Exception as e:
        error_message = f"Errore nel backup: {str(e)}"
        console.print(f"[red]{error_message}[/red]")
        log_console.print(f"BACKUP ERROR: {error_message}")
        return
    
    # Log di fine backup
    end_time = datetime.now()
    duration = end_time - start_time
    
    # Calcola dimensioni dell'archivio
    archive_size = "N/A"
    compression_ratio = "N/A"
    if os.path.exists(archive_path):
        size_bytes = os.path.getsize(archive_path)
        if size_bytes < 1024:
            archive_size = f"{size_bytes} B"
        elif size_bytes < 1024**2:
            archive_size = f"{size_bytes/1024:.1f} KB"
        elif size_bytes < 1024**3:
            archive_size = f"{size_bytes/(1024**2):.1f} MB"
        else:
            archive_size = f"{size_bytes/(1024**3):.1f} GB"
        
        # Calcola il rapporto di compressione se possibile
        try:
            with zipfile.ZipFile(archive_path, 'r') as zipf:
                total_uncompressed = sum(file_info.file_size for file_info in zipf.infolist())
                total_compressed = sum(file_info.compress_size for file_info in zipf.infolist())
                if total_uncompressed > 0:
                    ratio = (1 - total_compressed / total_uncompressed) * 100
                    compression_ratio = f"{ratio:.1f}%"
        except:
            compression_ratio = "N/A"
    
    final_message = f"=== BACKUP COMPLETATO - {end_time.strftime('%Y-%m-%d %H:%M:%S')} ==="
    summary_message = f"File processati: {total_files_copied} | Durata: {duration} | Dimensione: {archive_size}"
    compression_message = f"Compressione ottenuta: {compression_ratio} | Archivio: {archive_path}"
    
    console.rule(f"[bold green]{final_message}")
    console.print(f"[bold cyan]{summary_message}[/bold cyan]")
    console.print(f"[bold magenta]{compression_message}[/bold magenta]")
    
    log_console.rule(final_message)
    log_console.print(summary_message)
    log_console.print(compression_message)
    
    # Salva il log su file
    try:
        with open(log_path, 'w', encoding='utf-8') as log_file:
            log_file.write(log_buffer.getvalue())
        console.print(f"[bold magenta]Log salvato in: {log_path}[/bold magenta]")
    except Exception as e:
        console.print(f"[red]Errore nel salvare il log: {str(e)}[/red]")
    
    log_buffer.close()

# Esempio di utilizzo
if __name__ == "__main__":
    # Esempio di cartelle da fare il backup
    folders_to_backup = [
        r"C:\Users\Username\Documents",
        r"C:\Users\Username\Desktop",
        r"C:\Users\Username\Pictures"
    ]
    
    # Cartella dove salvare il backup
    backup_destination = r"D:\Backup"
    
    # Crea la cartella di destinazione se non esiste
    if not os.path.exists(backup_destination):
        os.makedirs(backup_destination)
    
    # Avvia il backup
    backup_folders(folders_to_backup, backup_destination)