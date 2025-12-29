import os
import re
from pathlib import Path

def clean_md_files(directory_path):
    # Регулярное выражение, объединяющее все паттерны
    pattern = re.compile(
        r'(^\{\%.*\%\}\s*$)|'  # шаблоны типа {% ... %}
        r'(^#+\s+)|'  # заголовки (#, ##, ###, ####)
        r'(\*\*)|'  # двойные звездочки
        r'(<(?:/?[^>]+)>\n?)|'  # HTML-теги
        r'(^---\s*$)|'  # разделители ---
        r'(^\*\*\*\s*$)|'  # разделители ***
        r'(^icon:.*$)|'  # метаданные icon
        r'(^description:.*$)|'  # метаданные description
        r'(^\n)|'  # пустые строки в начале
        r'(^\s*)',  # пустые строки в начале
        re.MULTILINE
    )
    
    # Путь к папке gitbook
    gitbook_path = Path(directory_path)
    
    # Найти все .md файлы
    md_files = list(gitbook_path.rglob("*.md"))
    
    if not md_files:
        print(f"Не найдено .md файлов в {directory_path}")
        return
    
    print(f"Найдено {len(md_files)} .md файлов")
    
    # Обработать каждый файл
    for md_file in md_files:
        try:
            # Прочитать содержимое файла
            with open(md_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Применить замену
            cleaned_content = pattern.sub('', content)
            
            # Записать обратно
            with open(md_file, 'w', encoding='utf-8') as f:
                f.write(cleaned_content)
            
            print(f"✓ Обработан: {md_file.relative_to(gitbook_path)}")
            
        except Exception as e:
            print(f"✗ Ошибка при обработке {md_file}: {e}")

if __name__ == "__main__":
    # Укажите путь к папке gitbook
    gitbook_folder = r".\gitbook"
    
    if os.path.exists(gitbook_folder):
        clean_md_files(gitbook_folder)
        print("\nГотово! Все файлы обработаны.")
    else:
        print(f"Папка {gitbook_folder} не найдена!")