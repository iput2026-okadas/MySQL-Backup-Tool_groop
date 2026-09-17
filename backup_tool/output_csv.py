
# libraries
from decimal import Decimal
from datetime import datetime, date, time, timedelta

import os
import csv
from pathlib import Path

# self-implementations
from backup_tool.mysql_source import MySQLSource

class CsvExport(MySQLSource):

    def __init__(
            self,
            config,
            table,
            directory,
        ):
        super().__init__(
            config,
        )
        self._table = table
        self._directory = directory
    
    def do_output(self):

    # this impl is copied from 'pushSample_csv&&dump.py'
    # of lines kinda 144 ~ 187
        os.makedirs(f"{self._directory}/data", exist_ok=True)
        with open(
            f"{self._directory}/data/{self._table}.csv",
            mode='w', newline='', encoding='utf-8'
        ) as csvfile:
            writer = csv.writer(csvfile)

            column_names = self.get_column_names(table_name=self._table)
            writer.writerow(column_names)
            column_types = self.get_column_types(table_name=self._table)
            writer.writerow(column_types)

            for raw_iter in self.iter_row_batches(self._table):
                for it in raw_iter:
                    self.debug(it)

                    line = []
                    for index, i in enumerate(it):
                        if i == None:
                            line.append("NULL")
                        elif isinstance(i, (int, float, bytes, bytearray, Decimal)):
                            line.append(str(i))
                        elif isinstance(i, (datetime, date, time, timedelta)):
                            line.append(repr(str(i)))
                        else:
                            line.append(repr(i))
                    writer.writerow(line)


        self.debug(f"backup data for the {self._table} finished")
