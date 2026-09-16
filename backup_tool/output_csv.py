
# libraries
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

    # this impl is cpied from 'pushSample_csv&&dump.py'
    # of lines kinda 144 ~ 187
        os.makedirs(f"{self._directory}/data", exist_ok=True)
        with open(
            f"{self._directory}/data/{self._table}.csv",
            mode='w', newline='', encoding='utf-8'
        ) as csvfile:
            writer = csv.writer(csvfile)

            column_names = self.get_column_types(table_name=self._table)
            writer.writerow(column_names)

            for raw_iter in self.iter_row_batches(self._table):
                for it in raw_iter:
                    self.debug(it)
                    writer.writerow(it)
                
                self.debug(f"{self._table}テーブルのデータをCSVファイルに書き込みました。")
