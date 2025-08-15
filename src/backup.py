import os
from dotenv import load_dotenv
from src.backup import backup_folders

def main():
    load_dotenv()
    
    folder_paths = os.getenv("FOLDER_PATHS").split(',')
    save_path = os.getenv("SAVE_PATH")
    
    backup_folders(folder_paths, save_path)

if __name__ == "__main__":
    main()