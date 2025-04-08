# src/treemapper/logger.py
import logging
import sys

# Убедимся, что имя логгера совпадает с именем пакета (хорошая практика)
# Но для простоты пока конфигурируем корневой логгер
# logger = logging.getLogger('treemapper')

def setup_logging(verbosity: int) -> None:
    """Configure the root logger based on verbosity."""
    level_map = {
        0: logging.ERROR,    # 40
        1: logging.WARNING,  # 30
        2: logging.INFO,     # 20
        3: logging.DEBUG     # 10
    }
    # Используем INFO как уровень по умолчанию, если verbosity некорректный
    level = level_map.get(verbosity, logging.INFO)

    # Получаем корневой логгер
    root_logger = logging.getLogger()

    # --- Более надежная конфигурация ---
    # 1. Устанавливаем уровень самого логгера
    root_logger.setLevel(level)

    # 2. Удаляем существующие обработчики (если есть), чтобы избежать дублирования
    #    Это важно при повторных вызовах в тестах или интерактивных сессиях
    # !!! ОСТОРОЖНО: Это может удалить обработчики, настроенные pytest или другими библиотеками.
    #    Возможно, лучше проверять наличие нашего специфичного хендлера перед добавлением.
    #    Или создавать дочерний логгер 'treemapper' и настраивать только его.
    # Пока оставим удаление для простоты в контексте этого приложения.
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)
        # handler.close() # Закрываем удаленный обработчик

    # 3. Создаем и добавляем новый обработчик (например, StreamHandler для вывода в консоль)
    #    По умолчанию basicConfig использует StreamHandler(sys.stderr), можно использовать stdout
    # handler = logging.StreamHandler(sys.stdout)
    # ИЛИ: чтобы соответствовать basicConfig по умолчанию:
    handler = logging.StreamHandler(sys.stderr)

    # 4. Устанавливаем уровень для обработчика (обычно совпадает с логгером или выше)
    handler.setLevel(level)

    # 5. Создаем форматтер
    formatter = logging.Formatter('%(levelname)s: %(message)s')

    # 6. Назначаем форматтер обработчику
    handler.setFormatter(formatter)

    # 7. Добавляем обработчик к логгеру
    root_logger.addHandler(handler)
    # --- Конец надежной конфигурации ---

    # Сообщение для проверки уровня (будет видно только если уровень DEBUG)
    logging.debug(f"Logging setup complete for root logger with level {level} ({logging.getLevelName(level)})")

    # Альтернатива: Попытка использовать basicConfig с force=True (Python 3.8+)
    # try:
    #     logging.basicConfig(
    #         level=level,
    #         format='%(levelname)s: %(message)s',
    #         stream=sys.stderr, # или sys.stdout
    #         force=True # Перезаписывает существующую конфигурацию
    #     )
    #     logging.debug(f"Logging setup via basicConfig(force=True) with level {level}")
    # except TypeError: # force появился в 3.8
    #     # Fallback для < 3.8 (менее надежный)
    #     logging.basicConfig(level=level, format='%(levelname)s: %(message)s', stream=sys.stderr)
    #     logging.warning("Python < 3.8, basicConfig might not reconfigure if already configured.")