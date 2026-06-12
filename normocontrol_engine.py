import os
import zipfile
import tempfile
import shutil
from pathlib import Path

import normocontrol
import dwg_converter
import office_checkers
import crypto_stamp

def check_file(file_path: str) -> dict:
    """Определяет тип файла и вызывает нужный чекер"""
    ext = file_path.lower().split('.')[-1]
    
    try:
        if ext == 'dxf':
            report = normocontrol.run_normocontrol(file_path)
        elif ext == 'dwg':
            dxf_path = dwg_converter.convert_dwg_to_dxf(file_path)
            report = normocontrol.run_normocontrol(dxf_path)
        elif ext == 'docx':
            report = office_checkers.check_docx(file_path)
        elif ext == 'xlsx':
            report = office_checkers.check_xlsx(file_path)
        elif ext == 'pdf':
            report = office_checkers.check_pdf(file_path)
        else:
            return {"passed": False, "error": f"Формат {ext} пока не поддерживается"}
            
        # Если проверка пройдена успешно, ставим крипто-штамп
        if report.get("passed", False):
            file_hash = crypto_stamp.compute_file_hash(file_path)
            stamp_info = crypto_stamp.register_stamp(Path(file_path).name, file_hash)
            report["stamp"] = stamp_info
            
        return report
        
    except Exception as e:
        return {"passed": False, "error": f"Внутренняя ошибка проверки: {str(e)}"}

def process_batch(input_path: str) -> dict:
    """Обрабатывает загруженный файл (одиночный или ZIP архив)"""
    results = {}
    
    if input_path.lower().endswith('.zip'):
        with tempfile.TemporaryDirectory() as extract_dir:
            try:
                with zipfile.ZipFile(input_path, 'r') as zip_ref:
                    zip_ref.extractall(extract_dir)
                    
                # Обходим все файлы в распакованной папке
                for root, _, files in os.walk(extract_dir):
                    for f in files:
                        file_path = os.path.join(root, f)
                        # Игнорируем скрытые файлы macOS
                        if f.startswith('._') or f == '.DS_Store':
                            continue
                        rel_name = os.path.relpath(file_path, extract_dir)
                        results[rel_name] = check_file(file_path)
            except zipfile.BadZipFile:
                return {"error": "Некорректный ZIP архив"}
    else:
        # Одиночный файл
        file_name = Path(input_path).name
        results[file_name] = check_file(input_path)
        
    # Формируем сводный отчет
    total_files = len(results)
    passed_files = sum(1 for r in results.values() if r.get("passed", False))
    
    return {
        "batch_summary": {
            "total": total_files,
            "passed": passed_files,
            "failed": total_files - passed_files
        },
        "files": results
    }
