from pathlib import Path

# Chemin absolu vers le répertoire sandbox et toutes les opérations sur les fichiers restent dans ce dossier.
SANDBOX_DIR = Path("sandbox").resolve()

#Vérifie que le chemin fourni se situe bien à l'intérieur du répertoire sandbox
def _check_sandbox(path: Path):
    if not str(path.resolve()).startswith(str(SANDBOX_DIR)):
        raise PermissionError("Accés en dehors du sandbox interdit") 
    

#Lit le contenu d'un fichier situé à l'intérieur du sandbox
def read_file(file_path: str) -> str:
    path = Path(file_path)
    # Vérification de sécurité : le fichier doit être dans le sandbox
    _check_sandbox(path)
    return path.read_text(encoding="utf-8")

#Écrit du contenu dans un fichier situé à l'intérieur du sandbox
def write_file(file_path: str, content: str):
    path = Path(file_path)
    _check_sandbox(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")