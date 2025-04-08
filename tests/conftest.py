# conftest.py
import shutil
import tempfile
from pathlib import Path
import sys # Добавлен для run_mapper sys.argv
import pytest


@pytest.fixture
def temp_project(tmp_path): # Используем встроенную фикстуру tmp_path pytest
    """Create a temporary project structure for testing."""
    # tmp_path автоматически создаст временную директорию и удалит ее
    temp_dir = tmp_path / "treemapper_test_project"
    temp_dir.mkdir()

    # Create a test project structure
    (temp_dir / "src").mkdir()
    (temp_dir / "src" / "main.py").write_text("def main():\n    print('hello')\n", encoding='utf-8')
    (temp_dir / "src" / "test.py").write_text("def test():\n    pass\n", encoding='utf-8')
    (temp_dir / "docs").mkdir()
    (temp_dir / "docs" / "readme.md").write_text("# Documentation\n", encoding='utf-8')
    (temp_dir / "output").mkdir() # Папка output для .treemapperignore
    (temp_dir / ".git").mkdir() # Папка .git
    (temp_dir / ".git" / "config").write_text("git config file", encoding='utf-8') # Файл внутри .git

    # Правила по умолчанию: игнорировать output/ и .git/
    (temp_dir / ".gitignore").write_text("*.pyc\n__pycache__/\n", encoding='utf-8')
    # ---> ИЗМЕНЕНИЕ: Добавляем .git/ сюда <---
    (temp_dir / ".treemapperignore").write_text("output/\n.git/\n", encoding='utf-8')

    yield temp_dir
    # shutil.rmtree не нужен, tmp_path сделает это сам


@pytest.fixture
def run_mapper(monkeypatch, temp_project):
    """Helper to run treemapper with given args."""

    def _run(args):
        """Runs the main function with patched CWD and sys.argv."""
        with monkeypatch.context() as m:
            # Меняем текущую директорию на временную директорию проекта
            m.chdir(temp_project)
            # Устанавливаем аргументы командной строки
            # sys.argv[0] должен быть именем скрипта/команды
            m.setattr(sys, "argv", ["treemapper"] + args)
            try:
                # Убедимся, что импортируем актуальную main
                # sys.path может потребовать очистки или добавления src,
                # но editable install должен решать это.
                from treemapper.treemapper import main
                main() # Вызываем main из импортированного модуля
                return True # Успешное выполнение без SystemExit(>0)
            except SystemExit as e:
                # Возвращаем False если код выхода не 0 (ошибка)
                if e.code != 0:
                    print(f"SystemExit caught with code: {e.code}") # Для отладки
                    return False
                return True # Успешное выполнение с SystemExit(0)
            except Exception as e:
                 print(f"Caught unexpected exception in run_mapper: {e}") # Отладка
                 # Можно добавить raise e, чтобы увидеть полный трейсбек в pytest
                 return False # Непредвиденная ошибка

    return _run