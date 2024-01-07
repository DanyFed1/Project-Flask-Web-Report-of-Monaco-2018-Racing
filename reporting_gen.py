import os
from typing import Dict, List, Optional
from dataclasses import dataclass, field
from datetime import datetime, timedelta
import re


@dataclass
class DriverLapInfo:
    """A class to represent a driver's information."""
    driver_init: str
    start_time: datetime
    end_time: datetime = field(init=False)
    driver_name: str = ""
    team: str = ""

    @property
    def driver_lap_time(self) -> Optional[timedelta]:
        # adding comparison as time data in end.log is not reliable, e.g. for
        # some driver end time is earlier then start time
        if self.end_time < self.start_time:
            return None
        else:
            return self.end_time - self.start_time


class Q1Processor:
    """ A class to process the Formula 1 Q1 lap times."""
    def __init__(self, folder_path: str) -> None:
        """
        Initialize the Q1Processor with paths to files.
        """
        self.start_log_path = os.path.join(folder_path, 'start.log')
        self.end_log_path = os.path.join(folder_path, 'end.log')
        self.txt_path = os.path.join(folder_path, 'abbreviations.txt')
        self.drivers = {}

    def read_log_file(self, file_path: str) -> Dict[str, datetime]:
        """Read a log file and return the data as a dictionary."""
        data = {}
        try:
            with open(file_path, 'r') as file:
                for line in file:
                    match = re.match(
                        r"([A-Z]{3})(\d{4}-\d{2}-\d{2}_\d{2}:\d{2}:\d{2}\.\d{3})",
                        line.strip())
                    if match:
                        driver_init, timestamp_str = match.groups()
                        timestamp = datetime.strptime(
                            timestamp_str, '%Y-%m-%d_%H:%M:%S.%f')
                        data[driver_init] = timestamp
        except IOError as e:
            print(f"Error reading file {file_path}: {e}")
        return data

    def integrate_driver_info(self) -> None:
        """Integrate driver information from the abbreviations file."""
        try:
            with open(self.txt_path, 'r') as file:
                for line in file:
                    driver_init, driver_name, team = line.strip().split('_')
                    if driver_init in self.drivers:
                        self.drivers[driver_init].driver_name = driver_name
                        self.drivers[driver_init].team = team
        except IOError as e:
            print(f"Error reading file {self.txt_path}: {e}")

    def process_files(self) -> None:
        """Process the start and end log files to populate the drivers dictionary."""
        start_times = self.read_log_file(self.start_log_path)
        end_times = self.read_log_file(self.end_log_path)

        for driver_init, start_time in start_times.items():
            driver_info = DriverLapInfo(driver_init, start_time)
            if driver_init in end_times:
                driver_info.end_time = end_times[driver_init]
            self.drivers[driver_init] = driver_info

        self.integrate_driver_info()


class Q1ReportGenerator:
    """A class to generate a report for the Formula 1 Q1 lap times."""

    def __init__(self, processor: Q1Processor) -> None:
        """Reporting is based on Q1Processor instance."""
        self.processor = processor
        self.processor.process_files()  # Process files upon initialization

    def rank_drivers(self, order: str = 'asc') -> List[DriverLapInfo]:
        """Rank the drivers based on their lap times, by default ranks asc"""
        drivers = [driver for driver in self.processor.drivers.values()]
        # Anomaly data should alway be the end of our classification.
        drivers.sort(
            key=lambda x: (
                x.driver_lap_time == None,
                x.driver_lap_time),
            reverse=(
                order == 'desc'))
        return drivers

    def print_report(self, order: str = 'asc') -> None:
        """Print the results of the Q1 based on order, by default ranks asc"""
        ranked_drivers = self.rank_drivers(order)
        print("Formula 1 - Qualifying Q1 Results\n")
        for i, driver in enumerate(ranked_drivers, start=1):
            if order == 'desc' and len(ranked_drivers) - i == 14:
                print("-" * 36 + 'ELIMINATED' + "-" * 36)
            elif order == 'asc' and i == 16:
                print("-" * 36 + 'ELIMINATED' + "-" * 36)
            time_str = driver.driver_lap_time
            if driver.driver_lap_time is not None:
                print(f"{i}. {driver.driver_name:<20} | {driver.team:<30} | {time_str}")
            else:
                print(f"{i}. {driver.driver_name:<20} | {driver.team:<30} | {'NO TIME COULD BE DETERMINED BASED ON INPUT FILES'}")


    def driver_info(self, driver_name: str) -> str:
        """Retrieve information for a specific driver."""
        for driver in self.processor.drivers.values():
            if driver.driver_name == driver_name:
                time_str = driver.driver_lap_time
                return f"{driver.driver_name:<20} | {driver.team:<30} | {time_str}"
        return f"Driver {driver_name} not found."

    #Adding new methods to return everything needed for Jinja Templates
    def get_report_data(self, order='asc'):
        """Get report data in a structured format for web rendering."""
        ranked_drivers = self.rank_drivers(order)
        report_data = []
        for i, driver in enumerate(ranked_drivers, start=1):
            driver_data = {
                'position': i,
                'name': driver.driver_name,
                'team': driver.team,
                'lap_time': str(driver.driver_lap_time) if driver.driver_lap_time else "NO TIME",
                'eliminated': i > 15
            }
            report_data.append(driver_data)
        return report_data

    def get_all_drivers(self):
        """Get a list of all drivers with their information."""
        return [{'code': driver.driver_init, 'name': driver.driver_name, 'team': driver.team}
                for driver in self.processor.drivers.values()]

    def get_driver_info(self, driver_init):
        """Get information for a specific driver."""
        driver = self.processor.drivers.get(driver_init)
        if driver:
            return {
                'name': driver.driver_name,
                'team': driver.team,
                'lap_time': str(driver.driver_lap_time) if driver.driver_lap_time else "NO TIME"
            }
        return None

