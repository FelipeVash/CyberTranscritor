#!/usr/bin/env python3
"""
Script para reorganizar a arquitetura do projeto conforme proposta.
Cria a estrutura de apps separados, move arquivos, ajusta imports e entry points.
Execute na raiz do projeto.
"""

import os
import shutil
import tarfile
from pathlib import Path
from datetime import datetime
import re

# ============================================================
# Configurações
# ============================================================
PROJECT_ROOT = Path(__file__).parent.absolute()

# Pastas a serem criadas
APPS_DIR = PROJECT_ROOT / "apps"
TRANSCRITOR_DIR = APPS_DIR / "transcritor"
MEETING_DIR = APPS_DIR / "meeting"
DEEPSEEK_DIR = APPS_DIR / "deepseek"

# Arquivos a serem movidos
MOVES = [
    # origem -> destino
    (PROJECT_ROOT / "core/frontend/main_window.py", TRANSCRITOR_DIR / "window.py"),
]

# Arquivos que devem ter seus imports ajustados (após movimentação)
FILES_TO_ADJUST = [
    TRANSCRITOR_DIR / "window.py",
    PROJECT_ROOT / "core/controller/app_controller.py",
    PROJECT_ROOT / "transcritor_app.py",
    PROJECT_ROOT / "meeting_app.py",
    PROJECT_ROOT / "deepseek_app.py",
]

# Pastas que podem ser removidas (se existirem)
TO_REMOVE = [
    PROJECT_ROOT / "transcritor_suite.egg-info",
    PROJECT_ROOT / "padronizar_estilos.py",
]

# ============================================================
# Funções auxiliares
# ============================================================
def create_backup():
    """Cria backup do projeto antes das alterações."""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_name = PROJECT_ROOT.parent / f"transcritor_backup_final_{timestamp}.tar.gz"
    print(f"📦 Criando backup em {backup_name}...")
    with tarfile.open(backup_name, "w:gz") as tar:
        for item in PROJECT_ROOT.iterdir():
            if item.name.startswith("venv") or item.name == "__pycache__" or item.name.endswith(".tar.gz"):
                continue
            tar.add(item, arcname=item.name)
    print(f"✅ Backup criado.")
    return backup_name

def ensure_dir(path):
    """Garante que o diretório existe."""
    path.mkdir(parents=True, exist_ok=True)

def safe_move(src, dst):
    """Move arquivo, criando diretório destino se necessário."""
    if not src.exists():
        print(f"⚠️  {src} não encontrado, ignorando.")
        return False
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.move(str(src), str(dst))
    print(f"✅ Movido {src} -> {dst}")
    return True

def adjust_imports_in_file(filepath):
    """Ajusta imports em um arquivo para refletir a nova estrutura."""
    if not filepath.exists():
        print(f"⚠️  {filepath} não encontrado, ignorando ajuste de imports.")
        return

    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read()

    # Substituições de imports
    replacements = [
        # Ajustar imports que apontavam para main_window (agora em apps.transcritor.window)
        (r"from core\.frontend\.main_window import", "from apps.transcritor.window import"),
        # Ajustar imports de dialogs, styles, etc. (continuam em core.frontend)
        # Nenhuma alteração necessária para esses, pois o caminho permanece o mesmo.
        # Ajustar referências a TranscriptionStudio se necessário (já está sendo importado como MainWindow)
    ]
    for pattern, repl in replacements:
        content = re.sub(pattern, repl, content, flags=re.MULTILINE)

    with open(filepath, "w", encoding="utf-8") as f:
        f.write(content)
    print(f"🔧 Imports ajustados em {filepath}")

def update_entry_points():
    """Atualiza os entry points (transcritor_app.py, meeting_app.py, deepseek_app.py) com os novos caminhos."""
    # transcritor_app.py
    transcritor_entry = PROJECT_ROOT / "transcritor_app.py"
    if transcritor_entry.exists():
        content = """#!/usr/bin/env python3
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from apps.transcritor.window import TranscriptionStudio as MainWindow
from core.controller.app_controller import AppController
from core.utils.logger import logger

def main():
    logger.info("Starting Cyberpunk Transcription Studio")
    controller = AppController()
    app = MainWindow(controller)
    app.root.mainloop()

if __name__ == "__main__":
    main()
"""
        with open(transcritor_entry, "w", encoding="utf-8") as f:
            f.write(content)
        print("✅ transcritor_app.py atualizado.")

    # meeting_app.py (verificar se já está correto)
    meeting_entry = PROJECT_ROOT / "meeting_app.py"
    if meeting_entry.exists():
        content = meeting_entry.read_text(encoding="utf-8")
        if "from apps.meeting.window import MeetingWindow" not in content:
            # substituir se necessário
            content = re.sub(
                r"from .* import MeetingWindow",
                "from apps.meeting.window import MeetingWindow",
                content
            )
            meeting_entry.write_text(content, encoding="utf-8")
            print("✅ meeting_app.py atualizado.")
        else:
            print("ℹ️ meeting_app.py já está correto.")

    # deepseek_app.py (verificar se já está correto)
    deepseek_entry = PROJECT_ROOT / "deepseek_app.py"
    if deepseek_entry.exists():
        content = deepseek_entry.read_text(encoding="utf-8")
        if "from apps.deepseek.window import DeepSeekWindow" not in content:
            content = re.sub(
                r"from .* import DeepSeekWindow",
                "from apps.deepseek.window import DeepSeekWindow",
                content
            )
            deepseek_entry.write_text(content, encoding="utf-8")
            print("✅ deepseek_app.py atualizado.")
        else:
            print("ℹ️ deepseek_app.py já está correto.")

def update_pyproject():
    """Atualiza pyproject.toml para incluir apps no find packages."""
    pyproject = PROJECT_ROOT / "pyproject.toml"
    if not pyproject.exists():
        print("⚠️ pyproject.toml não encontrado, pulando.")
        return

    content = pyproject.read_text(encoding="utf-8")
    # Procurar a seção [tool.setuptools.packages.find]
    if "[tool.setuptools.packages.find]" in content:
        # Verificar se já inclui "apps*"
        if 'include = ["core*", "apps*"]' not in content:
            # Tentar substituir a linha include
            content = re.sub(
                r'(include = \[)[^\]]*(\])',
                r'\1"core*", "apps*"\2',
                content,
                flags=re.DOTALL
            )
            pyproject.write_text(content, encoding="utf-8")
            print("✅ pyproject.toml atualizado.")
        else:
            print("ℹ️ pyproject.toml já está correto.")
    else:
        print("⚠️ Seção [tool.setuptools.packages.find] não encontrada. Adicione manualmente.")

def remove_unnecessary():
    """Remove pastas/arquivos desnecessários."""
    for item in TO_REMOVE:
        if item.exists():
            if item.is_dir():
                shutil.rmtree(item)
                print(f"🗑️  Removido diretório {item}")
            else:
                item.unlink()
                print(f"🗑️  Removido arquivo {item}")

# ============================================================
# Execução principal
# ============================================================
def main():
    print("🚀 Iniciando reorganização final da arquitetura...")
    resp = input("Deseja criar um backup antes? (s/N): ")
    if resp.lower() == 's':
        create_backup()

    # 1. Criar estrutura de pastas
    ensure_dir(APPS_DIR)
    ensure_dir(TRANSCRITOR_DIR)
    ensure_dir(MEETING_DIR)
    ensure_dir(DEEPSEEK_DIR)

    # Criar arquivos __init__.py
    for d in [APPS_DIR, TRANSCRITOR_DIR, MEETING_DIR, DEEPSEEK_DIR]:
        init_file = d / "__init__.py"
        if not init_file.exists():
            init_file.touch()
            print(f"✅ Criado {init_file}")

    # 2. Mover arquivos
    for src, dst in MOVES:
        safe_move(src, dst)

    # 3. Ajustar imports nos arquivos movidos e dependentes
    for filepath in FILES_TO_ADJUST:
        adjust_imports_in_file(filepath)

    # 4. Atualizar entry points
    update_entry_points()

    # 5. Atualizar pyproject.toml
    update_pyproject()

    # 6. Remover arquivos desnecessários
    remove_unnecessary()

    print("\n🎉 Reorganização concluída!")
    print("Verifique se os aplicativos funcionam executando:")
    print("  python transcritor_app.py")
    print("  python meeting_app.py")
    print("  python deepseek_app.py")
    print("  python launcher.py")
    print("\nExecute os testes: pytest tests/")

if __name__ == "__main__":
    main()