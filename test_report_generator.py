"""
Тесты для генератора отчетов.
"""

import pytest
import tempfile
import csv
import os
from pathlib import Path
from report_generator import (
    CSVReader,
    ReportFactory,
    PerformanceReport,
    parse_arguments
)


def create_test_csv(content: str, delimiter: str = ',') -> str:
    """Создает временный CSV файл для тестов."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', 
                                     delete=False, encoding='utf-8') as f:
        f.write(content)
        return f.name


class TestCSVReader:
    """Тесты для класса CSVReader"""
    
    def test_read_single_csv(self):
        """Тест чтения одного CSV файла."""
        content = """name,position,performance
Иван Иванов,Developer,85.5
Петр Петров,Manager,92.0
Анна Сидорова,Developer,78.3"""
        
        filename = create_test_csv(content)
        try:
            data = CSVReader.read_csv_files([filename])
            assert len(data) == 3
            assert data[0]['name'] == 'Иван Иванов'
            assert data[0]['position'] == 'Developer'
            assert data[0]['performance'] == '85.5'
        finally:
            os.unlink(filename)
    
    def test_read_multiple_csv(self):
        """Тест чтения нескольких CSV файлов."""
        content1 = """name,position,performance
Иван Иванов,Developer,85.5"""
        
        content2 = """name,position,performance
Петр Петров,Manager,92.0"""
        
        file1 = create_test_csv(content1)
        file2 = create_test_csv(content2)
        
        try:
            data = CSVReader.read_csv_files([file1, file2])
            assert len(data) == 2
            assert data[0]['name'] == 'Иван Иванов'
            assert data[1]['name'] == 'Петр Петров'
        finally:
            os.unlink(file1)
            os.unlink(file2)
    
    def test_file_not_found(self):
        """Тест обработки отсутствующего файла."""
        with pytest.raises(FileNotFoundError):
            CSVReader.read_csv_files(['nonexistent.csv'])
    
    def test_invalid_csv(self):
        """Тест обработки некорректного CSV."""
        content = """name,position,performance
Иван Иванов,Developer,85.5
некорректная,строка,без,правильного,количества,колонок"""
        
        filename = create_test_csv(content)
        try:
            # В зависимости от реализации, может возникнуть ошибка
            data = CSVReader.read_csv_files([filename])
            # Или успешное чтение с пропуском некорректных строк
            assert len(data) >= 1
        finally:
            os.unlink(filename)
    
    def test_csv_with_different_delimiters(self):
        """Тест чтения CSV с различными разделителями."""
        content = """name;position;performance
Иван Иванов;Developer;85.5
Петр Петров;Manager;92.0"""
        
        filename = create_test_csv(content, delimiter=';')
        try:
            data = CSVReader.read_csv_files([filename])
            assert len(data) == 2
            # Автоопределение разделителя должно работать
            assert data[0]['position'] == 'Developer'
        finally:
            os.unlink(filename)


class TestPerformanceReport:
    """Тесты для отчета по эффективности"""
    
    def test_generate_report_simple(self):
        """Тест генерации простого отчета."""
        data = [
            {'position': 'Developer', 'performance': '85.5'},
            {'position': 'Developer', 'performance': '78.3'},
            {'position': 'Manager', 'performance': '92.0'},
            {'position': 'Manager', 'performance': '88.0'},
        ]
        
        report = PerformanceReport()
        headers, rows = report.generate(data)
        
        assert headers == ['Position', 'Avg Performance']
        assert len(rows) == 2
        
        # Проверяем правильность вычислений
        developer_avg = (85.5 + 78.3) / 2
        manager_avg = (92.0 + 88.0) / 2
        
        # Находим соответствующие строки
        for position, avg in rows:
            if position == 'Developer':
                assert avg == round(developer_avg, 2)
            elif position == 'Manager':
                assert avg == round(manager_avg, 2)
        
        # Проверяем сортировку (по убыванию)
        assert rows[0][1] >= rows[1][1]
    
    def test_generate_report_with_invalid_data(self):
        """Тест с некорректными данными."""
        data = [
            {'position': 'Developer', 'performance': '85.5'},
            {'position': 'Developer', 'performance': 'invalid'},  # Некорректное значение
            {'position': '', 'performance': '92.0'},  # Пустая позиция
            {'position': 'Manager', 'performance': ''},  # Пустая эффективность
            {},  # Пустая строка
        ]
        
        report = PerformanceReport()
        headers, rows = report.generate(data)
        
        # Должна быть только одна валидная запись
        assert len(rows) == 1
        assert rows[0][0] == 'Developer'
        assert rows[0][1] == 85.5
    
    def test_generate_report_empty_data(self):
        """Тест с пустыми данными."""
        data = []
        report = PerformanceReport()
        headers, rows = report.generate(data)
        
        assert headers == ['Position', 'Avg Performance']
        assert len(rows) == 0
    
    def test_generate_report_single_position(self):
        """Тест с одной позицией."""
        data = [
            {'position': 'Developer', 'performance': '85.5'},
            {'position': 'Developer', 'performance': '90.0'},
            {'position': 'Developer', 'performance': '95.5'},
        ]
        
        report = PerformanceReport()
        headers, rows = report.generate(data)
        
        assert len(rows) == 1
        assert rows[0][0] == 'Developer'
        assert rows[0][1] == round((85.5 + 90.0 + 95.5) / 3, 2)


class TestReportFactory:
    """Тесты для фабрики отчетов"""
    
    def test_get_existing_report(self):
        """Тест получения существующего отчета."""
        report = ReportFactory.get_report('performance')
        assert isinstance(report, PerformanceReport)
    
    def test_get_nonexistent_report(self):
        """Тест получения несуществующего отчета."""
        with pytest.raises(ValueError, match="Отчет 'nonexistent' не найден"):
            ReportFactory.get_report('nonexistent')
    
    def test_list_reports(self):
        """Тест получения списка отчетов."""
        reports = ReportFactory.list_reports()
        assert 'performance' in reports
        assert isinstance(reports, list)


class TestArgumentParser:
    """Тесты парсера аргументов"""
    
    def test_parse_valid_arguments(self):
        """Тест валидных аргументов."""
        test_args = [
            '--files', 'file1.csv', 'file2.csv',
            '--report', 'performance'
        ]
        
        # Мокаем sys.argv
        import sys
        original_argv = sys.argv
        try:
            sys.argv = ['report_generator.py'] + test_args
            args = parse_arguments()
            
            assert args.files == ['file1.csv', 'file2.csv']
            assert args.report == 'performance'
            assert args.output_format == 'table'
        finally:
            sys.argv = original_argv
    
    def test_parse_missing_required_arguments(self):
        """Тест отсутствия обязательных аргументов."""
        test_args = ['--files', 'file1.csv']
        
        import sys
        original_argv = sys.argv
        try:
            sys.argv = ['report_generator.py'] + test_args
            with pytest.raises(SystemExit):
                parse_arguments()
        finally:
            sys.argv = original_argv
    
    def test_parse_list_reports(self):
        """Тест аргумента list-reports."""
        test_args = ['--list-reports']
        
        import sys
        original_argv = sys.argv
        try:
            sys.argv = ['report_generator.py'] + test_args
            args = parse_arguments()
            assert args.list_reports == True
        finally:
            sys.argv = original_argv


@pytest.fixture
def sample_data_files():
    """Фикстура для создания временных файлов с данными."""
    files = []
    
    # Первый файл
    content1 = """name,position,performance,project
Иван Иванов,Developer,85.5,Project A
Петр Петров,Manager,92.0,Project B
Анна Сидорова,Developer,78.3,Project A"""
    
    # Второй файл
    content2 = """name,position,performance,project
Мария Петрова,Developer,88.0,Project B
Алексей Смирнов,Manager,95.5,Project A
Ольга Иванова,Developer,82.7,Project C"""
    
    file1 = create_test_csv(content1)
    file2 = create_test_csv(content2)
    files = [file1, file2]
    
    yield files
    
    # Очистка
    for file in files:
        if os.path.exists(file):
            os.unlink(file)


def test_integration(sample_data_files):
    """Интеграционный тест: чтение файлов и генерация отчета."""
    # Чтение данных
    data = CSVReader.read_csv_files(sample_data_files)
    assert len(data) == 6
    
    # Генерация отчета
    report = PerformanceReport()
    headers, rows = report.generate(data)
    
    # Проверяем результаты
    assert headers == ['Position', 'Avg Performance']
    assert len(rows) == 2  # Developer и Manager
    
    # Проверяем вычисления
    developer_performances = [85.5, 78.3, 88.0, 82.7]
    manager_performances = [92.0, 95.5]
    
    developer_avg = sum(developer_performances) / len(developer_performances)
    manager_avg = sum(manager_performances) / len(manager_performances)
    
    for position, avg in rows:
        if position == 'Developer':
            assert avg == round(developer_avg, 2)
        elif position == 'Manager':
            assert avg == round(manager_avg, 2)
    
    # Проверяем сортировку (Manager должен быть первым)
    assert rows[0][0] == 'Manager'
    assert rows[1][0] == 'Developer'


def test_edge_cases():
    """Тест граничных случаев."""
    # Тест с очень большими числами
    data = [
        {'position': 'Developer', 'performance': '999999.99'},
        {'position': 'Developer', 'performance': '0.01'},
    ]
    
    report = PerformanceReport()
    headers, rows = report.generate(data)
    
    assert len(rows) == 1
    expected_avg = round((999999.99 + 0.01) / 2, 2)
    assert rows[0][1] == expected_avg
    
    # Тест с отрицательными значениями
    data = [
        {'position': 'Tester', 'performance': '-10.0'},
        {'position': 'Tester', 'performance': '10.0'},
    ]
    
    headers, rows = report.generate(data)
    assert rows[0][1] == 0.0  # (-10 + 10) / 2 = 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
