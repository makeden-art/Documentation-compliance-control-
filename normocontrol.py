import math
from typing import List, Dict, Any
import ezdxf

# ГОСТ 2.304-81 Шрифты чертежные. Стандартные высоты.
GOST_TEXT_HEIGHTS = [1.8, 2.5, 3.5, 5.0, 7.0, 10.0, 14.0, 20.0, 28.0, 40.0]
# Допустимая погрешность высоты текста (например, из-за округлений в автокаде)
HEIGHT_TOLERANCE = 0.1 

# Популярные шрифты по ГОСТу
GOST_FONTS = [
    "isocpeur", "isocpeur italic", "gost type a", "gost type b",
    "cs_gost2304", "mipgost", "gost", "gost_a", "gost_b"
]

def check_text_height(height: float) -> bool:
    for std_h in GOST_TEXT_HEIGHTS:
        if math.isclose(height, std_h, abs_tol=HEIGHT_TOLERANCE):
            return True
    return False

def check_font_name(font_file: str) -> bool:
    if not font_file:
        return False
    font_lower = font_file.lower().replace(".ttf", "").replace(".shx", "").strip()
    return any(g in font_lower for g in GOST_FONTS)

def run_normocontrol(file_path: str) -> Dict[str, Any]:
    """
    Проверяет DXF файл на соответствие базовым требованиям нормоконтроля.
    Возвращает словарь со списком ошибок и предупреждений.
    """
    try:
        doc = ezdxf.readfile(file_path)
    except Exception as e:
        return {"error": f"Ошибка чтения DXF файла: {e}"}

    msp = doc.modelspace()
    
    errors = []
    warnings = []
    
    # 1. Проверка текстовых стилей на ГОСТ-шрифты
    valid_styles = set()
    invalid_styles = set()
    
    for style in doc.styles:
        # ezdxf style attributes: dxf.name, dxf.font
        name = style.dxf.name
        font_file = style.dxf.font
        
        # Ignored standard system styles if they are empty
        if not font_file:
            continue
            
        if check_font_name(font_file):
            valid_styles.add(name)
        else:
            invalid_styles.add(name)
            warnings.append(f"Стиль текста '{name}' использует не ГОСТ-шрифт: {font_file}")

    # 2. Проверка примитивов в ModelSpace
    bad_height_count = 0
    entities_on_zero_layer = 0
    entities_on_defpoints = 0
    
    for entity in msp:
        layer = entity.dxf.layer
        
        # Проверка слоев
        if layer == "0":
            entities_on_zero_layer += 1
        elif layer.lower() == "defpoints":
            entities_on_defpoints += 1
            
        # Проверка текстов
        if entity.dxftype() in ["TEXT", "MTEXT"]:
            height = getattr(entity.dxf, 'height', None)
            # Для MTEXT высота может быть в dxf.char_height
            if height is None and entity.dxftype() == "MTEXT":
                height = getattr(entity.dxf, 'char_height', None)
                
            if height is not None:
                if not check_text_height(height):
                    bad_height_count += 1
                    errors.append(
                        f"Нестандартная высота текста: {height:.2f} "
                        f"(Слой: '{layer}', Тип: {entity.dxftype()})"
                    )
            
            # Проверка стиля у конкретного текста
            style_name = getattr(entity.dxf, 'style', 'Standard')
            if style_name in invalid_styles:
                # Мы уже добавили предупреждение про сам стиль, 
                # можно не дублировать для каждого текста, или считать статистику
                pass

    if entities_on_zero_layer > 0:
        errors.append(f"Найдено {entities_on_zero_layer} объектов на слое '0' (Слой '0' предназначен только для создания блоков).")
    
    if entities_on_defpoints > 0:
        errors.append(f"Найдено {entities_on_defpoints} объектов на слое 'Defpoints' (На этом слое ничего нельзя чертить).")

    # Сводим результаты
    passed = len(errors) == 0
    
    return {
        "passed": passed,
        "errors": errors[:50], # Ограничиваем вывод, чтобы не спамить
        "total_errors": len(errors),
        "warnings": warnings,
        "total_warnings": len(warnings)
    }
