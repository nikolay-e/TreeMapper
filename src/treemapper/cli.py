# src/treemapper/cli.py
import argparse
import sys
from pathlib import Path
from typing import Tuple


def parse_args() -> Tuple[Path | None, Path | None, Path | None, bool, int]:
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        prog='treemapper', # <--- ДОБАВЛЕНО ЭТО
        description="Generate a YAML representation of a directory structure.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter)

    parser.add_argument(
        "directory",
        nargs="?",
        default=".",
        help="The directory to analyze")

    parser.add_argument(
        "-i", "--ignore-file",
        default=None,
        help="Path to the custom ignore file (optional)")

    parser.add_argument(
        "-o", "--output-file",
        default="./directory_tree.yaml",
        help="Path to the output YAML file")

    parser.add_argument(
        "--no-default-ignores",
        action="store_true",
        help="Disable default ignores (.treemapperignore, .gitignore, output file)") # Уточнено описание

    parser.add_argument(
        "-v", "--verbosity",
        type=int,
        choices=range(0, 4),
        default=2,
        metavar="[0-3]",
        help="Set verbosity level (0: ERROR, 1: WARNING, 2: INFO, 3: DEBUG)")

    args = parser.parse_args()

    # Проверяем директорию
    try:
        root_dir = Path(args.directory).resolve(strict=True) # strict=True проверит существование
        if not root_dir.is_dir():
            # Эта проверка может быть избыточна с strict=True, но оставим для ясности
            print(f"Error: The path '{root_dir}' is not a valid directory.", file=sys.stderr)
            sys.exit(1)
    except FileNotFoundError:
         print(f"Error: The directory '{args.directory}' does not exist.", file=sys.stderr)
         sys.exit(1)
    except Exception as e: # Другие возможные ошибки resolve
         print(f"Error resolving directory path '{args.directory}': {e}", file=sys.stderr)
         sys.exit(1)

    # Обрабатываем путь к файлу вывода
    output_file = Path(args.output_file)
    if not output_file.is_absolute():
        # Берем текущую рабочую директорию ДО ее возможного изменения в тестах
        output_file = Path.cwd() / output_file
    # Не резолвим output_file здесь, т.к. он может еще не существовать

    # Обрабатываем путь к ignore-файлу
    ignore_file_path = Path(args.ignore_file) if args.ignore_file else None
    if ignore_file_path and not ignore_file_path.is_absolute():
         ignore_file_path = Path.cwd() / ignore_file_path
    # Не резолвим ignore_file здесь, проверка на существование будет в ignore.py

    # Возвращаем resolved root_dir и подготовленные output_file/ignore_file
    return root_dir, ignore_file_path, output_file, args.no_default_ignores, args.verbosity