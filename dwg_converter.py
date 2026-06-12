import os
import subprocess
import tempfile
import shutil
from pathlib import Path

def convert_dwg_to_dxf(input_file: str) -> str:
    """
    Конвертирует файл DWG в DXF с помощью ODAFileConverter.
    Возвращает путь к сгенерированному DXF файлу.
    Если произошла ошибка, выбрасывает Exception.
    """
    input_path = Path(input_file)
    if not input_path.exists():
        raise FileNotFoundError(f"Файл {input_file} не найден.")

    # ODAFileConverter работает с директориями, а не отдельными файлами
    # Создаем временную директорию для входа и выхода
    with tempfile.TemporaryDirectory(prefix="oda_in_") as in_dir, \
         tempfile.TemporaryDirectory(prefix="oda_out_") as out_dir:
        
        # Копируем входной файл во входящую директорию
        temp_input_path = Path(in_dir) / input_path.name
        shutil.copy2(input_path, temp_input_path)

        # Формируем команду вызова ODAFileConverter
        # Синтаксис: ODAFileConverter <InputDir> <OutDir> <Version> <OutFormat> <Recurse> <Audit> [InputFilter]
        cmd = [
            "xvfb-run", "-a", "ODAFileConverter",
            in_dir,
            out_dir,
            "ACAD2018", # Выходная версия (надежная современная версия)
            "DXF",      # Формат
            "0",        # Без рекурсии
            "1",        # С аудитом (исправление ошибок)
            "*.dwg"     # Фильтр
        ]

        try:
            # Запускаем конвертер
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
            if result.returncode != 0:
                # ODAFileConverter может вернуть код 0 даже при ошибке конвертации,
                # но если он упал, проверяем код
                raise RuntimeError(f"ODAFileConverter завершился с ошибкой: {result.stderr}")
        except subprocess.TimeoutExpired:
            raise RuntimeError("Превышено время ожидания конвертации DWG в DXF (60 сек).")
        except FileNotFoundError:
            raise RuntimeError("Утилита ODAFileConverter не найдена на сервере.")

        # Проверяем, появился ли файл в выходной директории
        out_files = list(Path(out_dir).glob("*.dxf"))
        if not out_files:
            raise RuntimeError(f"Не удалось конвертировать файл. Лог: {result.stdout}\n{result.stderr}")

        # Копируем результат обратно во временную папку оригинального файла
        output_dxf = input_path.with_suffix('.dxf')
        shutil.copy2(out_files[0], output_dxf)

        return str(output_dxf)
