# tests/utils.py
import pytest
import yaml
from pathlib import Path
from typing import Dict, Any, List, Set, Hashable

def load_yaml(path: Path) -> Dict[str, Any]:
    """Load YAML file and return its contents."""
    try:
        with path.open('r', encoding='utf-8') as f:
            # Используем SafeLoader для безопасности
            return yaml.load(f, Loader=yaml.SafeLoader)
    except FileNotFoundError:
        pytest.fail(f"Output YAML file not found: {path}")
    except Exception as e:
        pytest.fail(f"Failed to load or parse YAML file {path}: {e}")


def get_all_files_in_tree(node: Dict[str, Any]) -> Set[str]:
    """Recursively get all file and directory names from the loaded tree structure."""
    names = set()
    if not isinstance(node, dict) or "name" not in node:
         return names # Защита от некорректной структуры

    names.add(node["name"])
    if "children" in node and isinstance(node["children"], list):
        for child in node["children"]:
            # Добавим проверку, что child - это словарь перед рекурсией
            if isinstance(child, dict):
                 names.update(get_all_files_in_tree(child))
    return names

def find_node_by_path(tree: Dict[str, Any], path_segments: List[str]) -> Dict[str, Any] | None:
    """Find a node in the tree by list of path segments relative to root node."""
    current_node = tree
    for segment in path_segments:
        if current_node is None or "children" not in current_node or not isinstance(current_node["children"], list):
            return None # No children to search within or current node invalid

        found_child = None
        for child in current_node["children"]:
            if isinstance(child, dict) and child.get("name") == segment:
                found_child = child
                break # Нашли нужного ребенка на этом уровне

        if found_child is None:
             return None # Сегмент не найден на этом уровне
        current_node = found_child # Переходим к найденному ребенку

    return current_node # Дошли до конца, возвращаем найденный узел


# ---> НАЧАЛО ДОБАВЛЕНИЯ <---
def make_hashable(obj: Any) -> Hashable:
    """Recursively convert dicts and lists to hashable tuples."""
    if isinstance(obj, dict):
        # Преобразуем словарь в отсортированный кортеж пар (ключ, хешируемое_значение)
        return tuple(sorted((k, make_hashable(v)) for k, v in obj.items()))
    if isinstance(obj, list):
         # Преобразуем список в кортеж хешируемых значений
        return tuple(make_hashable(item) for item in obj)
    # bool и None уже хешируемы
    if isinstance(obj, (str, int, float, bool, type(None))):
         return obj
    # Если тип не известен, пытаемся хешировать, иначе вызываем ошибку
    try:
         hash(obj)
         return obj
    except TypeError:
        # Для неизвестных нехешируемых типов можно вернуть строковое представление или ошибку
        # Это важно, если в дереве могут быть другие типы данных
        # print(f"Warning: Cannot make type {type(obj)} hashable, returning str representation.")
        return repr(obj) # Или raise TypeError(f"Cannot make type {type(obj)} hashable")

# ---> КОНЕЦ ДОБАВЛЕНИЯ <---