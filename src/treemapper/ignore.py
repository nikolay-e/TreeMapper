# src/treemapper/ignore.py
import logging
import os
from pathlib import Path
from typing import List, Dict, Tuple

import pathspec


def read_ignore_file(file_path: Path) -> List[str]:
    """Read the ignore patterns from the specified ignore file."""
    ignore_patterns = []
    if file_path.is_file():
        try:
            # Explicitly use utf-8 for reading ignore files
            with file_path.open('r', encoding='utf-8') as f:
                ignore_patterns = [line.strip() for line in f
                                   if line.strip() and not line.startswith('#')]
            logging.info(f"Using ignore patterns from {file_path}")
            logging.debug(f"Read ignore patterns from {file_path}: {ignore_patterns}")
        except IOError as e:
             logging.warning(f"Could not read ignore file {file_path}: {e}")
        except UnicodeDecodeError as e:
             logging.warning(f"Could not decode ignore file {file_path} as UTF-8: {e}")
    return ignore_patterns


def load_pathspec(patterns: List[str], syntax='gitwildmatch') -> pathspec.PathSpec:
    """Load pathspec from a list of patterns."""
    spec = pathspec.PathSpec.from_lines(syntax, patterns)
    logging.debug(f"Loaded pathspec with patterns: {patterns}")
    return spec


def get_ignore_specs(
    root_dir: Path,
    custom_ignore_file: Path | None = None,
    no_default_ignores: bool = False,
    output_file: Path | None = None
) -> Tuple[pathspec.PathSpec, Dict[Path, pathspec.PathSpec]]:
    """Get combined ignore specs and git ignore specs."""
    default_patterns = get_default_patterns(root_dir, no_default_ignores, output_file)
    custom_patterns = get_custom_patterns(root_dir, custom_ignore_file)

    # Determine combined patterns based on no_default_ignores flag
    if no_default_ignores:
        # Only use custom patterns + output file ignore (if applicable and INSIDE root)
        combined_patterns = custom_patterns
        if output_file:
             try:
                 resolved_output = output_file.resolve()
                 resolved_root = root_dir.resolve()
                 if resolved_output.is_relative_to(resolved_root): # Check if output is inside root
                     relative_output_str = resolved_output.relative_to(resolved_root).as_posix()
                     output_pattern = f"/{relative_output_str}" # Pattern relative to root
                     if output_pattern not in combined_patterns: # Avoid duplicates if specified in custom
                         combined_patterns.append(output_pattern)
                         logging.debug(f"Adding output file to ignores (no_default_ignores=True): {output_pattern}")
             except ValueError: # Not relative
                 pass
             except Exception as e:
                 logging.warning(f"Could not determine relative path for output file {output_file}: {e}")
    else:
         # Combine default and custom patterns
        combined_patterns = default_patterns + custom_patterns

    # ---> ЛОГИРОВАНИЕ ДЛЯ ДИАГНОСТИКИ <---
    logging.debug(f"Ignore specs params: no_default_ignores={no_default_ignores}")
    logging.debug(f"Default patterns (used unless no_default_ignores): {default_patterns}")
    logging.debug(f"Custom patterns (-i): {custom_patterns}")
    logging.debug(f"Combined patterns for spec: {combined_patterns}")
    # ---> КОНЕЦ ЛОГИРОВАНИЯ <---

    combined_spec = load_pathspec(combined_patterns)
    gitignore_specs = get_gitignore_specs(root_dir, no_default_ignores)

    return combined_spec, gitignore_specs


def get_default_patterns(root_dir: Path, no_default_ignores: bool, output_file: Path | None) -> List[str]:
    """Retrieve default ignore patterns ONLY IF no_default_ignores is FALSE."""
    if no_default_ignores:
        # This function shouldn't even be called by get_ignore_specs if True,
        # but double-check for safety. Or rely on get_ignore_specs logic.
        # Let's return empty to be safe if called directly somehow.
        return []

    patterns = []
    # Add patterns from .treemapperignore (located in root_dir)
    treemapper_ignore_file = root_dir / ".treemapperignore"
    patterns.extend(read_ignore_file(treemapper_ignore_file))

    # Add the output file to ignore patterns IF it's inside root_dir
    if output_file:
        try:
            resolved_output = output_file.resolve()
            resolved_root = root_dir.resolve()
            # Check if output is inside root_dir using is_relative_to (Python 3.9+)
            # Use try/except ValueError for compatibility or if check fails
            try:
                 relative_output = resolved_output.relative_to(resolved_root)
                 # Add only the file itself, starting with / to anchor to root
                 output_pattern = f"/{relative_output.as_posix()}"
                 patterns.append(output_pattern)
                 logging.debug(f"Adding output file to default ignores: {output_pattern}")
                 # --- УДАЛЕНО ИГНОРИРОВАНИЕ РОДИТЕЛЬСКОЙ ПАПКИ ---
            except ValueError:
                 # Output file is outside root_dir, no need to add to default ignores
                 logging.debug(f"Output file {output_file} is outside root directory {root_dir}, not adding to default ignores.")

        except Exception as e: # Catch potential resolve() or other errors
            logging.warning(f"Could not determine relative path for output file {output_file}: {e}")

    return patterns


def get_custom_patterns(root_dir: Path, custom_ignore_file: Path | None) -> List[str]:
    """Retrieve custom ignore patterns from the file specified with -i."""
    if not custom_ignore_file:
        return []

    # Resolve custom ignore file path relative to CWD if not absolute
    # Note: If run_mapper changes CWD, this might need adjustment depending on expected behavior.
    # Assuming custom_ignore_file path is relative to where the command is run.
    if not custom_ignore_file.is_absolute():
        custom_ignore_file = Path.cwd() / custom_ignore_file

    if custom_ignore_file.is_file():
        return read_ignore_file(custom_ignore_file)
    else:
        # Log warning only if the file was explicitly provided but not found
        logging.warning(f"Custom ignore file '{custom_ignore_file}' not found.")
        return []


def get_gitignore_specs(root_dir: Path, no_default_ignores: bool) -> Dict[Path, pathspec.PathSpec]:
    """Retrieve gitignore specs for all .gitignore files found within root_dir."""
    if no_default_ignores:
        return {} # Do not load any .gitignore files if flag is set

    gitignore_specs = {}
    try:
        for dirpath_str, dirnames, filenames in os.walk(root_dir, topdown=True):
            # Avoid recursing into directories that should be ignored by parent specs
            # (basic protection, full gitignore precedence is complex)
            # This requires passing parent specs down, making it much more complex.
            # For now, we load all found .gitignores. A simple optimization:
            if '.git' in dirnames:
                dirnames.remove('.git') # Don't recurse into .git

            if ".gitignore" in filenames:
                gitignore_path = Path(dirpath_str) / ".gitignore"
                patterns = read_ignore_file(gitignore_path)
                if patterns: # Only load spec if there are actual patterns
                    gitignore_specs[Path(dirpath_str)] = load_pathspec(patterns)

    except OSError as e:
         logging.warning(f"Error walking directory {root_dir} to find .gitignore files: {e}")

    return gitignore_specs


def should_ignore(relative_path_str: str, combined_spec: pathspec.PathSpec) -> bool:
    """Check if a file or directory should be ignored based on combined pathspec."""
    # pathspec should handle directory matching correctly if patterns end with '/'
    # We primarily need to check the path itself. Checking parents might over-ignore.
    # Let's simplify: only check the path string itself.
    # Ensure directories passed from build_tree end with '/'
    is_ignored = combined_spec.match_file(relative_path_str)

    # Optional: Check without trailing slash if it's a directory? Pathspec might do this.
    # if relative_path_str.endswith('/') and not is_ignored:
    #     is_ignored = combined_spec.match_file(relative_path_str.rstrip('/'))

    logging.debug(f"Checking combined spec ignore for '{relative_path_str}': {is_ignored}")
    return is_ignored