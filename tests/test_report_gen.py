from unittest.mock import patch, mock_open
import reporting_gen as rpg
from datetime import datetime, timedelta
import pytest

# Sample data input for testing
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

# Mock datetime for consistent testing
MOCK_DATETIME = datetime(2018, 5, 24, 12, 0, 0)


@pytest.fixture
def mock_datetime_now(monkeypatch):
    class MockDateTime(datetime):
        @classmethod
        def now(cls):
            return MOCK_DATETIME

    monkeypatch.setattr(datetime, 'now', MockDateTime.now)


class TestQ1Processor:
    @patch("builtins.open", new_callable=mock_open, read_data=SAMPLE_START_LOG)
    def test_read_start_log(self, mock_file):
        processor = rpg.Q1Processor("/some/path")
        start_times = processor.read_log_file(processor.start_log_path)
        assert len(start_times) == 2
        assert start_times["SVF"] == datetime(2018, 5, 24, 12, 2, 58, 917)

    @patch("builtins.open", new_callable=mock_open, read_data=SAMPLE_END_LOG)
    def test_read_end_log(self, mock_file):
        processor = rpg.Q1Processor("/some/path")
        end_times = processor.read_log_file(processor.end_log_path)
        assert len(end_times) == 2
        assert end_times["SVF"] == datetime(2018, 5, 24, 12, 4, 3, 332)

    @patch("builtins.open", new_callable=mock_open,
           read_data=SAMPLE_ABBREVIATIONS_TXT)
    def test_integrate_driver_info(self, mock_file):
        processor = rpg.Q1Processor("/some/path")
        processor.drivers = {"SVF": rpg.DriverLapInfo("SVF", MOCK_DATETIME)}
        processor.integrate_driver_info()
        assert processor.drivers["SVF"].driver_name == "Sebastian Vettel"
        assert processor.drivers["SVF"].team == "FERRARI"

    @patch("report_gen.Q1Processor.read_log_file")
    @patch("report_gen.Q1Processor.integrate_driver_info")
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
    @patch("report_gen.Q1Processor.process_files")
    def test_rank_drivers(self, mock_process_files):
        processor = rpg.Q1Processor("/some/path")
        processor.drivers = {
            "SVF": rpg.DriverLapInfo(
                "SVF", datetime(
                    2018, 5, 24, 12, 2, 58, 917)), "NHR": rpg.DriverLapInfo(
                "NHR", datetime(
                    2018, 5, 24, 12, 2, 49, 914))}
        processor.drivers["SVF"].end_time = datetime(
            2018, 5, 24, 12, 4, 3, 332)
        processor.drivers["SVF"].driver_name = "Sebastian Vettel"
        processor.drivers["SVF"].team = "FERRARI"
        processor.drivers["NHR"].end_time = datetime(
            2018, 5, 24, 12, 4, 2, 979)
        processor.drivers["NHR"].driver_name = "Nico Hulkenberg"
        processor.drivers["NHR"].team = "RENAULT"

        report_generator = rpg.Q1ReportGenerator(processor)
        ranked_drivers = report_generator.rank_drivers()
        assert len(ranked_drivers) == 2
        assert ranked_drivers[0].driver_name == "Sebastian Vettel"

    def test_get_report_data(self, mock_datetime_now):
        processor = rpg.Q1Processor("/some/path")
        processor.drivers = {
            "SVF": rpg.DriverLapInfo(
                "SVF",
                MOCK_DATETIME,
                MOCK_DATETIME +
                timedelta(
                    minutes=2)),
            "NHR": rpg.DriverLapInfo(
                "NHR",
                MOCK_DATETIME,
                MOCK_DATETIME +
                timedelta(
                    minutes=1))}
        processor.drivers["SVF"].driver_name = "Sebastian Vettel"
        processor.drivers["SVF"].team = "FERRARI"
        processor.drivers["NHR"].driver_name = "Nico Hulkenberg"
        processor.drivers["NHR"].team = "RENAULT"

        report_generator = rpg.Q1ReportGenerator(processor)
        report_data = report_generator.get_report_data()
        assert len(report_data) == 2
        assert report_data[0]['name'] == "Nico Hulkenberg"  # NHR is faster

    def test_get_all_drivers(self):
        processor = rpg.Q1Processor("/some/path")
        processor.drivers = {
            "SVF": rpg.DriverLapInfo(
                "SVF",
                MOCK_DATETIME,
                MOCK_DATETIME +
                timedelta(
                    minutes=2)),
            "NHR": rpg.DriverLapInfo(
                "NHR",
                MOCK_DATETIME,
                MOCK_DATETIME +
                timedelta(
                    minutes=1))}
        processor.drivers["SVF"].driver_name = "Sebastian Vettel"
        processor.drivers["SVF"].team = "FERRARI"
        processor.drivers["NHR"].driver_name = "Nico Hulkenberg"
        processor.drivers["NHR"].team = "RENAULT"

        report_generator = rpg.Q1ReportGenerator(processor)
        all_drivers = report_generator.get_all_drivers()
        assert len(all_drivers) == 2
        assert all_drivers[0]['name'] == "Sebastian Vettel"

    def test_get_driver_info(self):
        processor = rpg.Q1Processor("/some/path")
        processor.drivers = {
            "SVF": rpg.DriverLapInfo(
                "SVF",
                MOCK_DATETIME,
                MOCK_DATETIME +
                timedelta(
                    minutes=2))}
        processor.drivers["SVF"].driver_name = "Sebastian Vettel"
        processor.drivers["SVF"].team = "FERRARI"

        report_generator = rpg.Q1ReportGenerator(processor)
        driver_info = report_generator.get_driver_info("SVF")
        assert driver_info['name'] == "Sebastian Vettel"
        assert driver_info['team'] == "FERRARI"
