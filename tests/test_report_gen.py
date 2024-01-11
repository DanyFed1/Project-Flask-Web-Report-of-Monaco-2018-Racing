import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from unittest.mock import patch, mock_open
import reporting_gen as rpg
from datetime import datetime


# Sample data inpit for testing
SAMPLE_START_LOG = """
SVF2018-05-24_12:02:58.917
NHR2018-05-24_12:02:49.914
"""

SAMPLE_END_LOG = """
SVF2018-05-24_12:04:03.332
NHR2018-05-24_12:04:02.979
"""

SAMPLE_ABBREVIATIONS_TXT = """
SVF_Sebastian Vettel_FERRARI
NHR_Nico Hulkenberg_RENAULT
""".strip()


class TestQ1Processor:
    @patch("builtins.open", new_callable=mock_open, read_data=SAMPLE_START_LOG)
    def test_read_start_log(self, mock_file):
        processor = rpg.Q1Processor("/some/path")
        start_times = processor.read_log_file(processor.start_log_path)
        assert len(start_times) == 2
        assert start_times["SVF"] is not None

    @patch("builtins.open", new_callable=mock_open, read_data=SAMPLE_END_LOG)
    def test_read_end_log(self, mock_file):
        processor = rpg.Q1Processor("/some/path")
        end_times = processor.read_log_file(processor.end_log_path)
        assert len(end_times) == 2
        assert end_times["SVF"] is not None

    @patch("builtins.open", new_callable=mock_open,
           read_data=SAMPLE_ABBREVIATIONS_TXT)
    def test_integrate_driver_info(self, mock_file):
        processor = rpg.Q1Processor("/some/path")
        processor.drivers = {"SVF": rpg.DriverLapInfo("SVF", datetime.now())}
        processor.integrate_driver_info()
        assert processor.drivers["SVF"].driver_name == "Sebastian Vettel"
        assert processor.drivers["SVF"].team == "FERRARI"

    @patch("reporting_gen.Q1Processor.read_log_file")
    @patch("reporting_gen.Q1Processor.integrate_driver_info")
    def test_process_files(self, mock_integrate, mock_read_log):
        mock_read_log.side_effect = [
            {"SVF": datetime(2018, 5, 24, 12, 2, 58, 917)},
            {"SVF": datetime(2018, 5, 24, 12, 4, 3, 332)}
        ]
        processor = rpg.Q1Processor("/some/path")
        processor.process_files()
        assert "SVF" in processor.drivers
        assert processor.drivers["SVF"].start_time == datetime(
            2018, 5, 24, 12, 2, 58, 917)


class TestQ1ReportGenerator:
    @patch("reporting_gen.Q1Processor.process_files")
    def test_rank_drivers(self, mock_process_files):
        processor = rpg.Q1Processor("/some/path")
        processor.drivers = {
            "SVF": rpg.DriverLapInfo("SVF", datetime(2018, 5, 24, 12, 2, 58, 917)),
            "NHR": rpg.DriverLapInfo("NHR", datetime(2018, 5, 24, 12, 2, 49, 914))
        }
        processor.drivers["SVF"].end_time = datetime(2018, 5, 24, 12, 4, 3, 332)
        processor.drivers["SVF"].driver_name = "Sebastian Vettel"
        processor.drivers["SVF"].team = "FERRARI"
        processor.drivers["NHR"].end_time = datetime(2018, 5, 24, 12, 4, 2, 979)
        processor.drivers["NHR"].driver_name = "Nico Hulkenberg"
        processor.drivers["NHR"].team = "RENAULT"

        report_generator = rpg.Q1ReportGenerator(processor)
        ranked_drivers = report_generator.rank_drivers()
        assert len(ranked_drivers) > 0

    def test_print_report(self, capsys):
        processor = rpg.Q1Processor("/some/path")
        processor.drivers = {
            "SVF": rpg.DriverLapInfo("SVF", datetime(2018, 5, 24, 12, 2, 58, 917)),
            "NHR": rpg.DriverLapInfo("NHR", datetime(2018, 5, 24, 12, 2, 49, 914))
        }
        processor.drivers["SVF"].end_time = datetime(2018, 5, 24, 12, 4, 3, 332)
        processor.drivers["SVF"].driver_name = "Sebastian Vettel"
        processor.drivers["SVF"].team = "FERRARI"
        processor.drivers["NHR"].end_time = datetime(2018, 5, 24, 12, 4, 2, 979)
        processor.drivers["NHR"].driver_name = "Nico Hulkenberg"
        processor.drivers["NHR"].team = "RENAULT"

        report_generator = rpg.Q1ReportGenerator(processor)
        report_generator.print_report()
        captured = capsys.readouterr()
        assert "Sebastian Vettel" in captured.out
        assert "FERRARI" in captured.out

    def test_driver_info(self):
        processor = rpg.Q1Processor("/some/path")
        processor.drivers = {
            "SVF": rpg.DriverLapInfo("SVF", datetime(2018, 5, 24, 12, 2, 58, 917))
        }
        processor.drivers["SVF"].end_time = datetime(2018, 5, 24, 12, 4, 3, 332)
        processor.drivers["SVF"].driver_name = "Sebastian Vettel"
        processor.drivers["SVF"].team = "FERRARI"

        report_generator = rpg.Q1ReportGenerator(processor)
        info = report_generator.driver_info("Sebastian Vettel")
        assert "Sebastian Vettel" in info
        assert "FERRARI" in info

    def test_get_report_data(self):
        processor = rpg.Q1Processor("/some/path")
        processor.drivers = {
            "SVF": rpg.DriverLapInfo("SVF", datetime(2018, 5, 24, 12, 2, 58, 917), "Sebastian Vettel", "FERRARI"),
            "NHR": rpg.DriverLapInfo("NHR", datetime(2018, 5, 24, 12, 2, 49, 914), "Nico Hulkenberg", "RENAULT")
        }
        processor.drivers["SVF"].end_time = datetime(2018, 5, 24, 12, 4, 3, 332)
        processor.drivers["NHR"].end_time = datetime(2018, 5, 24, 12, 4, 2, 979)

        report_generator = rpg.Q1ReportGenerator(processor)
        report_data = report_generator.get_report_data('asc')
        assert len(report_data) > 0
        assert 'position' in report_data[0]
        assert 'name' in report_data[0]
        assert 'team' in report_data[0]
        assert 'lap_time' in report_data[0]

    def test_get_all_drivers(self):
        processor = rpg.Q1Processor("/some/path")
        processor.drivers = {
            "SVF": rpg.DriverLapInfo("SVF", datetime(2018, 5, 24, 12, 2, 58, 917), "Sebastian Vettel", "FERRARI"),
            "NHR": rpg.DriverLapInfo("NHR", datetime(2018, 5, 24, 12, 2, 49, 914), "Nico Hulkenberg", "RENAULT")
        }
        processor.drivers["SVF"].end_time = datetime(2018, 5, 24, 12, 4, 3, 332)
        processor.drivers["NHR"].end_time = datetime(2018, 5, 24, 12, 4, 2, 979)

        report_generator = rpg.Q1ReportGenerator(processor)
        drivers = report_generator.get_all_drivers()
        assert len(drivers) > 0
        assert 'code' in drivers[0]
        assert 'name' in drivers[0]
        assert 'team' in drivers[0]

    def test_get_driver_info(self):
        processor = rpg.Q1Processor("/some/path")
        # Populate processor with sample data
        processor.drivers = {
            "SVF": rpg.DriverLapInfo("SVF", datetime(2018, 5, 24, 12, 2, 58, 917))
        }
        processor.drivers["SVF"].end_time = datetime(2018, 5, 24, 12, 4, 3, 332)
        processor.drivers["SVF"].driver_name = "Sebastian Vettel"
        processor.drivers["SVF"].team = "FERRARI"

        report_generator = rpg.Q1ReportGenerator(processor)
        driver_info = report_generator.get_driver_info("SVF")
        assert driver_info['name'] == "Sebastian Vettel"
        assert driver_info['team'] == "FERRARI"

#Usage:
# export PYTHONPATH=$PYTHONPATH:$(pwd)
# pytest tests/test_report_gen.py