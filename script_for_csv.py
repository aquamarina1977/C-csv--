#!/usr/bin/env python3
"""
Генератор отчетов из CSV файлов.
Поддерживает различные типы отчетов.
"""

import argparse
import csv
import sys
from collections import defaultdict
from pathlib import Path
from typing import Dict, List, Tuple, Any, Optional


class CSVReader:
    """Класс для чтения CSV файлов"""
    
    @staticmethod
    def read_csv_files(file_paths: List[str]) -> List[Dict[str, Any]]:
        """
        Читает данные из нескольких CSV файлов.
        
        Args:
            file_paths: Список путей к CSV файлам
            
        Returns:
            Список словарей с данными из всех файлов
            
        Raises:
            FileNotFoundError: Если файл не найден
            ValueError: Если файл имеет неверный формат
        """
        all_data = []
        
        for file_path in file_paths:
            path = Path(file_path)
            if not path.exists():
                raise FileNotFoundError(f"Файл не найден: {file_path}")
            
            try:
                with open(path, 'r', encoding='utf-8') as file:
                    # Автоопределение разделителя
                    sample = file.read(1024)
                    file.seek(0)
                    
                    # Проверяем, есть ли заголовки
                    has_header = csv.Sniffer().has_header(sample)
                    
                    if has_header:
                        dialect = csv.Sniffer().sniff(sample)
                        reader = csv.DictReader(file, dialect=dialect)
                    else:
                        # Если нет заголовков, используем стандартные
                        reader = csv.DictReader(file, fieldnames=None)
                    
                    file_data = list(reader)
                    all_data.extend(file_data)
                    
            except csv.Error as e:
                raise ValueError(f"Ошибка чтения CSV файла {file_path}: {e}")
            except UnicodeDecodeError:
                # Пробуем другую кодировку
                try:
                    with open(path, 'r', encoding='cp1251') as file:
                        reader = csv.DictReader(file)
                        file_data = list(reader)
                        all_data.extend(file_data)
                except:
                    raise ValueError(f"Не удалось прочитать файл {file_path}. Проверьте кодировку.")
        
        return all_data


class ReportGenerator:
    """Базовый класс для генерации отчетов"""
    
    def generate(self, data: List[Dict[str, Any]]) -> Tuple[List[str], List[List[Any]]]:
        """
        Генерирует отчет из данных.
        
        Args:
            data: Список словарей с данными
            
        Returns:
            Кортеж (заголовки, строки данных)
            
        Raises:
            NotImplementedError: Метод должен быть реализован в подклассах
        """
        raise NotImplementedError("Метод generate должен быть реализован в подклассе")


class PerformanceReport(ReportGenerator):
    """Генератор отчета по эффективности"""
    
    def generate(self, data: List[Dict[str, Any]]) -> Tuple[List[str], List[List[Any]]]:
        """
        Генерирует отчет по эффективности.
        Группирует данные по позициям и вычисляет среднюю эффективность.
        
        Args:
            data: Список словарей с данными
            
        Returns:
            Кортеж (заголовки, строки данных)
        """
        # Словарь для хранения данных по позициям
        position_data = defaultdict(list)
        
        for row in data:
            # Проверяем наличие необходимых полей
            position = row.get('position', '').strip()
            performance_str = row.get('performance', '').strip()
            
            if position and performance_str:
                try:
                    performance = float(performance_str)
                    position_data[position].append(performance)
                except (ValueError, TypeError):
                    # Пропускаем некорректные значения
                    continue
        
        # Вычисляем среднюю эффективность для каждой позиции
        report_rows = []
        for position, performances in position_data.items():
            if performances:  # Проверяем, что есть данные
                avg_performance = sum(performances) / len(performances)
                report_rows.append([position, round(avg_performance, 2)])
        
        # Сортируем по эффективности (по убыванию)
        report_rows.sort(key=lambda x: x[1], reverse=True)
        
        headers = ["Position", "Avg Performance"]
        return headers, report_rows


class ReportFactory:
    """Фабрика для создания отчетов"""
    
    _reports = {
        'performance': PerformanceReport,
        # Здесь можно добавить новые отчеты
        # 'skills': SkillsReport,
        # 'timeline': TimelineReport,
    }
    
    @classmethod
    def get_report(cls, report_name: str) -> ReportGenerator:
        """
        Создает отчет по имени.
        
        Args:
            report_name: Название отчета
            
        Returns:
            Экземпляр генератора отчетов
            
        Raises:
            ValueError: Если отчет с таким именем не найден
        """
        report_class = cls._reports.get(report_name.lower())
        if not report_class:
            raise ValueError(f"Отчет '{report_name}' не найден. "
                           f"Доступные отчеты: {', '.join(cls._reports.keys())}")
        return report_class()
    
    @classmethod
    def register_report(cls, report_name: str, report_class):
        """
        Регистрирует новый тип отчета.
        
        Args:
            report_name: Название отчета
            report_class: Класс отчета
            
        Raises:
            ValueError: Если отчет с таким именем уже существует
        """
        if report_name in cls._reports:
            raise ValueError(f"Отчет '{report_name}' уже зарегистрирован")
        cls._reports[report_name] = report_class
    
    @classmethod
    def list_reports(cls) -> List[str]:
        """Возвращает список доступных отчетов"""
        return list(cls._reports.keys())


def parse_arguments():
    """Парсит аргументы командной строки"""
    parser = argparse.ArgumentParser(
        description='Генератор отчетов из CSV файлов',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Примеры использования:
  %(prog)s --files data1.csv data2.csv --report performance
  %(prog)s -f tasks.csv -r performance
        """
    )
    
    parser.add_argument(
        '--files', '-f',
        nargs='+',
        required=True,
        help='Пути к CSV файлам с данными'
    )
    
    parser.add_argument(
        '--report', '-r',
        required=True,
        help=f'Название отчета. Доступные: {", ".join(ReportFactory.list_reports())}'
    )
    
    parser.add_argument(
        '--output-format',
        choices=['table', 'csv', 'json'],
        default='table',
        help='Формат вывода (по умолчанию: table)'
    )
    
    parser.add_argument(
        '--delimiter',
        default=',',
        help='Разделитель в CSV файлах (по умолчанию: запятая)'
    )
    
    parser.add_argument(
        '--list-reports',
        action='store_true',
        help='Показать список доступных отчетов'
    )
    
    return parser.parse_args()


def print_table(headers: List[str], rows: List[List[Any]]):
    """
    Выводит таблицу в консоль.
    
    Args:
        headers: Заголовки столбцов
        rows: Строки данных
    """
    try:
        from tabulate import tabulate
        print(tabulate(rows, headers=headers, tablefmt="grid"))
    except ImportError:
        # Если tabulate не установлен, используем простой вывод
        print("Установите библиотеку tabulate для красивого вывода таблиц")
        print("pip install tabulate")
        
        # Простой вывод
        header_line = " | ".join(headers)
        print(header_line)
        print("-" * len(header_line))
        for row in rows:
            print(" | ".join(str(item) for item in row))


def main():
    """Основная функция скрипта"""
    args = parse_arguments()
    
    if args.list_reports:
        print("Доступные отчеты:")
        for report in ReportFactory.list_reports():
            print(f"  - {report}")
        return 0
    
    try:
        # Читаем данные из файлов
        reader = CSVReader()
        data = reader.read_csv_files(args.files)
        
        if not data:
            print("Внимание: файлы не содержат данных")
            return 1
        
        # Создаем отчет
        report_generator = ReportFactory.get_report(args.report)
        headers, rows = report_generator.generate(data)
        
        if not rows:
            print("Отчет не содержит данных")
            return 0
        
        # Выводим результат
        if args.output_format == 'table':
            print_table(headers, rows)
        elif args.output_format == 'csv':
            import csv as csv_module
            writer = csv_module.writer(sys.stdout)
            writer.writerow(headers)
            writer.writerows(rows)
        elif args.output_format == 'json':
            import json
            result = []
            for row in rows:
                result.append(dict(zip(headers, row)))
            print(json.dumps(result, indent=2, ensure_ascii=False))
        
        print(f"\nВсего обработано записей: {len(data)}")
        print(f"Отчет содержит записей: {len(rows)}")
        
    except FileNotFoundError as e:
        print(f"Ошибка: {e}", file=sys.stderr)
        return 1
    except ValueError as e:
        print(f"Ошибка: {e}", file=sys.stderr)
        return 1
    except Exception as e:
        print(f"Непредвиденная ошибка: {e}", file=sys.stderr)
        return 1
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
