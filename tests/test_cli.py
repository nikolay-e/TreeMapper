# tests/test_cli.py
import pytest
import subprocess
import sys
from pathlib import Path

# Предполагаем, что load_yaml есть в tests.utils
from .utils import load_yaml

# Получаем путь к исполняемому файлу python в текущем окружении
PYTHON_EXEC = sys.executable

def run_cli_command(args, cwd):
    """ Запускает treemapper как отдельный процесс """
    command = [PYTHON_EXEC, "-m", "treemapper"] + args
    # Используем subprocess для запуска, т.к. run_mapper не ловит stdout/stderr легко
    # и не проверяет флаг -h
    result = subprocess.run(command, capture_output=True, text=True, cwd=cwd, encoding='utf-8')
    return result

def test_cli_help_short(temp_project):
    """Тест: вызов справки через -h"""
    result = run_cli_command(["-h"], cwd=temp_project)
    assert result.returncode == 0
    assert "usage: treemapper" in result.stdout.lower()
    assert "--help" in result.stdout
    assert "--output-file" in result.stdout
    assert "--verbosity" in result.stdout

def test_cli_help_long(temp_project):
    """Тест: вызов справки через --help"""
    result = run_cli_command(["--help"], cwd=temp_project)
    assert result.returncode == 0
    assert "usage: treemapper" in result.stdout.lower()
    assert "--help" in result.stdout

def test_cli_invalid_verbosity(temp_project, capsys):
    """Тест: неверный уровень verbosity"""
    # argparse должен сам выдать ошибку и завершиться с кодом > 0
    # run_mapper должен вернуть False
    # Или можно использовать run_cli_command и проверить stderr
    result = run_cli_command(["-v", "5"], cwd=temp_project)
    assert result.returncode != 0
    assert "invalid choice: 5" in result.stderr # argparse пишет ошибки в stderr

    result_neg = run_cli_command(["-v", "-1"], cwd=temp_project)
    assert result_neg.returncode != 0
    assert "invalid choice: -1" in result_neg.stderr

def test_cli_version_display(temp_project):
    """Тест: отображение версии (если будет добавлено)"""
    # Пока такой опции нет, но можно добавить
    pytest.skip("Version display option ('--version') not implemented yet.")
    # Пример, если добавите:
    # from treemapper.version import __version__
    # result = run_cli_command(["--version"], cwd=temp_project)
    # assert result.returncode == 0
    # assert __version__ in result.stdout