#!/usr/bin/env python3
"""
Script de reorganização da suíte de aplicativos com backup automático e recriação de ambientes.
Move arquivos para as pastas core/ e apps/meeting/, ajusta imports, remove lixos e recria ambientes.
Execute na raiz do projeto.
"""

import os
import shutil
import re
import tarfile
import subprocess
import sys
from pathlib import Path
from datetime import datetime

# ============================================================
# Configurações
# ============================================================
PROJECT_ROOT = Path(__file__).parent.absolute()

# Pastas que serão criadas
CORE_DIR = PROJECT_ROOT / "core"
APPS_DIR = PROJECT_ROOT / "apps"
MEETING_DIR = APPS_DIR / "meeting"

# Pastas e arquivos a serem completamente removidos (lixo)
TO_DELETE = [
    ".pytest_cache",
    "__pycache__",
    "venv_transcritor",
    "venv_meeting",
    "venv",
    "yay",
    "logs",
    ".coverage",
    "htmlcov",
    "*.tar.gz",
    "=4.0.3",
    "python_version.txt",  # opcional, remover se não quiser versionar
]

# Padrões de arquivos a remover (usando glob)
DELETE_PATTERNS = ["**/__pycache__", "**/*.pyc", "**/*.pyo", "**/*.log"]

# Mapeamento de diretórios fonte para destino dentro de core/
SOURCE_TO_CORE = {
    "backend": "core/backend",
    "frontend": "core/frontend",
    "controller": "core/controller",
    "utils": "core/utils",
    "config.py": "core/config.py",
    # outros arquivos que devem ir para core
}

# Arquivos específicos do meeting (serão movidos para apps/meeting/)
MEETING_FILES = [
    "controller/meeting_controller.py",
    "frontend/meeting_window.py",
]

# Entry points que devem permanecer na raiz (serão ajustados)
ENTRY_POINTS = ["main_app.py", "meeting_app.py"]

# Pastas a serem excluídas do backup (para não ocupar espaço)
BACKUP_EXCLUDE = [
    "venv*",
    "__pycache__",
    ".pytest_cache",
    "yay",
    "logs",
    "*.tar.gz",
]

# Configurações dos ambientes virtuais
ENVS = [
    {
        "name": "venv_transcritor",
        "python_version": "3.12",  # ajuste conforme sua necessidade
        "requirements": ["requirements-base.txt", "requirements-dev.txt"],
        "entry_point": "main_app.py"
    },
    {
        "name": "venv_meeting",
        "python_version": "3.14",  # ajuste conforme sua necessidade
        "requirements": ["requirements-meeting.txt"],
        "entry_point": "meeting_app.py"
    },
]

# ============================================================
# Funções auxiliares
# ============================================================
def create_backup():
    """Cria um backup compactado do projeto, excluindo pastas desnecessárias."""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_name = PROJECT_ROOT.parent / f"transcritor_backup_{timestamp}.tar.gz"
    
    print(f"📦 Criando backup em {backup_name}...")
    
    with tarfile.open(backup_name, "w:gz") as tar:
        for item in PROJECT_ROOT.iterdir():
            should_exclude = False
            for pattern in BACKUP_EXCLUDE:
                if pattern.endswith("*") and item.name.startswith(pattern[:-1]):
                    should_exclude = True
                    break
                elif pattern == item.name:
                    should_exclude = True
                    break
            if not should_exclude:
                tar.add(item, arcname=item.name)
    
    print(f"✅ Backup criado: {backup_name}")
    return backup_name

def safe_move(src, dst):
    """Move arquivo ou diretório, criando diretórios pai se necessário."""
    src_path = PROJECT_ROOT / src
    dst_path = PROJECT_ROOT / dst
    if not src_path.exists():
        print(f"⚠️  Aviso: {src} não encontrado, ignorando.")
        return
    dst_path.parent.mkdir(parents=True, exist_ok=True)
    shutil.move(str(src_path), str(dst_path))
    print(f"✅ Movido {src} -> {dst}")

def adjust_imports_in_file(filepath):
    """Ajusta imports no arquivo: substitui referências antigas pelas novas."""
    if not filepath.exists():
        return
    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read()

    # Substituições de imports
    replacements = [
        (r"\bbackend\.", "core.core.backend."),
        (r"\bfrontend\.", "core.core.frontend."),
        (r"\bcontroller\.(?!meeting_controller\b)", "core.core.controller."),
        (r"\butils\.", "core.core.utils."),
        (r"^\s*import\s+config\b", "from core import config"),
        (r"^\s*from\s+config\s+import\s+", "from core.config import "),
        (r"from\s+controller\.meeting_controller\s+import", "from apps.meeting.controller import"),
        (r"from\s+frontend\.meeting_window\s+import", "from apps.meeting.window import"),
    ]
    for pattern, repl in replacements:
        content = re.sub(pattern, repl, content, flags=re.MULTILINE)

    with open(filepath, "w", encoding="utf-8") as f:
        f.write(content)
    print(f"🔧 Imports ajustados em {filepath}")

def remove_unnecessary():
    """Remove pastas e arquivos indesejados."""
    for pattern in DELETE_PATTERNS:
        for path in PROJECT_ROOT.glob(pattern):
            if path.is_dir():
                shutil.rmtree(path)
                print(f"🗑️  Removido diretório {path}")
            elif path.is_file():
                path.unlink()
                print(f"🗑️  Removido arquivo {path}")
    for name in TO_DELETE:
        path = PROJECT_ROOT / name
        if path.exists():
            if path.is_dir():
                shutil.rmtree(path)
                print(f"🗑️  Removido diretório {path}")
            elif path.is_file():
                path.unlink()
                print(f"🗑️  Removido arquivo {path}")

def create_launcher():
    """Cria o launcher.py se não existir."""
    launcher_path = PROJECT_ROOT / "launcher.py"
    if launcher_path.exists():
        print("ℹ️  launcher.py já existe, ignorando.")
        return
    content = '''#!/usr/bin/env python3
import tkinter as tk
from tkinter import ttk
import subprocess
import sys
from pathlib import Path

BASE_DIR = Path(__file__).parent

def launch_app(script_name, venv_name):
    if sys.platform == "win32":
        python_exe = BASE_DIR / venv_name / "Scripts" / "python.exe"
    else:
        python_exe = BASE_DIR / venv_name / "bin" / "python"
    script_path = BASE_DIR / script_name
    if not python_exe.exists():
        print(f"Ambiente virtual {venv_name} não encontrado.")
        return
    subprocess.Popen([str(python_exe), str(script_path)])

root = tk.Tk()
root.title("Suíte Transcritor")
root.geometry("400x300")
root.resizable(False, False)

frame = ttk.Frame(root, padding=20)
frame.pack(fill=tk.BOTH, expand=True)

ttk.Label(frame, text="Escolha um aplicativo:", font=("Arial", 14)).pack(pady=10)

ttk.Button(frame, text="🎤 Transcritor / Tradutor",
           command=lambda: launch_app("main_app.py", "venv_transcritor"),
           width=30).pack(pady=5)

ttk.Button(frame, text="🎙️ Meeting Recorder",
           command=lambda: launch_app("meeting_app.py", "venv_meeting"),
           width=30).pack(pady=5)

ttk.Button(frame, text="🤖 DeepSeek Chat (em breve)",
           state="disabled", width=30).pack(pady=5)

root.mainloop()
'''
    with open(launcher_path, "w", encoding="utf-8") as f:
        f.write(content)
    os.chmod(launcher_path, 0o755)
    print("✅ launcher.py criado.")

def update_entry_points():
    """Atualiza os imports nos entry points (main_app.py e meeting_app.py)."""
    for ep in ENTRY_POINTS:
        ep_path = PROJECT_ROOT / ep
        if not ep_path.exists():
            print(f"⚠️  Entry point {ep} não encontrado, ignorando.")
            continue
        adjust_imports_in_file(ep_path)

def check_python_version(version):
    """Verifica se um executável python com a versão especificada está disponível."""
    python_cmd = f"python{version}"
    try:
        subprocess.run([python_cmd, "--version"], capture_output=True, check=True)
        return python_cmd
    except (subprocess.CalledProcessError, FileNotFoundError):
        return None

def create_virtualenv(env_name, python_cmd):
    """Cria um ambiente virtual usando o comando python especificado."""
    env_path = PROJECT_ROOT / env_name
    if env_path.exists():
        print(f"ℹ️  Ambiente {env_name} já existe, removendo para recriar...")
        shutil.rmtree(env_path)
    print(f"🔧 Criando ambiente virtual {env_name} com {python_cmd}...")
    subprocess.run([python_cmd, "-m", "venv", str(env_path)], check=True)
    return env_path

def install_requirements(env_path, req_files):
    """Instala os requisitos no ambiente virtual."""
    if sys.platform == "win32":
        pip = env_path / "Scripts" / "pip"
    else:
        pip = env_path / "bin" / "pip"
    
    for req_file in req_files:
        req_path = PROJECT_ROOT / req_file
        if not req_path.exists():
            print(f"⚠️  Arquivo de requisitos {req_file} não encontrado, ignorando.")
            continue
        print(f"📦 Instalando {req_file} em {env_path.name}...")
        subprocess.run([str(pip), "install", "-r", str(req_path)], check=True)

def run_tests(env_path):
    """Executa os testes (pytest) no ambiente virtual."""
    if sys.platform == "win32":
        python = env_path / "Scripts" / "python"
    else:
        python = env_path / "bin" / "python"
    
    # Verifica se pytest está instalado
    result = subprocess.run([str(python), "-m", "pytest", "--version"], capture_output=True)
    if result.returncode != 0:
        print("⚠️  pytest não encontrado, instalando...")
        subprocess.run([str(python), "-m", "pip", "install", "pytest"], check=True)
    
    print(f"🧪 Executando testes no ambiente {env_path.name}...")
    subprocess.run([str(python), "-m", "pytest", "tests/"])

def recreate_environments():
    """Recria os ambientes virtuais com as configurações especificadas."""
    print("\n🔧 Recriando ambientes virtuais...")
    for env in ENVS:
        python_cmd = check_python_version(env["python_version"])
        if not python_cmd:
            print(f"❌ Python {env['python_version']} não encontrado no sistema. Instale-o e tente novamente.")
            continue
        env_path = create_virtualenv(env["name"], python_cmd)
        install_requirements(env_path, env["requirements"])
        # Opcional: rodar testes
        run_tests(env_path)
    print("✅ Ambientes recriados.")

# ============================================================
# Execução principal
# ============================================================
def main():
    print("🚀 Iniciando reorganização do projeto...")
    print("⚠️  Certifique-se de ter feito um backup antes de continuar.")
    response = input("Deseja criar um backup do projeto atual? (s/N): ")
    if response.lower() == 's':
        create_backup()
    else:
        print("⏭️  Backup ignorado pelo usuário.")
    
    response = input("Deseja prosseguir com a reorganização? (s/N): ")
    if response.lower() != 's':
        print("Operação cancelada.")
        return

    # Criar pastas de destino
    CORE_DIR.mkdir(exist_ok=True)
    MEETING_DIR.mkdir(parents=True, exist_ok=True)

    # Mover diretórios compartilhados para core/
    for src, dst in SOURCE_TO_CORE.items():
        safe_move(src, dst)

    # Mover arquivos específicos do meeting para apps/meeting/
    for f in MEETING_FILES:
        src = f
        dst = f"apps/meeting/{Path(f).name}"
        safe_move(src, dst)

    # Ajustar imports em todos os arquivos .py dentro de core/ e apps/
    for py_file in PROJECT_ROOT.glob("**/*.py"):
        if any(ign in str(py_file) for ign in ["venv", "__pycache__", ".pytest_cache", "yay"]):
            continue
        adjust_imports_in_file(py_file)

    # Atualizar entry points
    update_entry_points()

    # Criar launcher
    create_launcher()

    # Remover lixos
    remove_unnecessary()

    print("\n🎉 Reorganização concluída!")
    
    # Perguntar se deseja recriar os ambientes
    response = input("Deseja recriar os ambientes virtuais agora? (s/N): ")
    if response.lower() == 's':
        recreate_environments()
    else:
        print("⏭️  Ambientes não recriados. Lembre-se de recriá-los manualmente.")

if __name__ == "__main__":
    main()