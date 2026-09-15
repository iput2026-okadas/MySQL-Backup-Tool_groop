# libraries
from decimal import Decimal
from datetime import datetime, date, time, timedelta

import io
import zipfile
import csv

# self-implementations
from s3_source import S3Source


def s3_multipart_upload(source: S3Source,tables: list[str],plains: list[str],sql_no_data=False,) -> None:

    source.connect()
    buffer = io.BytesIO()

    with zipfile.ZipFile(buffer,mode="a",compression=zipfile.ZIP_DEFLATED,
    ) as zf:

        for t in tables:
            # SQL出力
            source.debug(f"parse table: {t} into .sql")
            target_file = f"schema/{t}.sql"

            with zf.open(target_file, mode="w") as f:
                f.write(b"\n")
                f.write(f"DROP TABLE IF EXISTS {t};\n".encode("utf-8"))
                f.write(source.get_create_table(t)[0][1].encode("utf-8"))
                f.write(b";\n\n")

                source.debug(column_types := source.get_column_types(t))
                if not sql_no_data:
                    f.write(f"LOCK TABLES {t} WRITE;\n".encode("utf-8"))
                    for raw_iter in source.iter_row_batches(t):
                        source.debug(raw_iter)

                        for row in raw_iter:
                            insert = f"INSERT INTO {t} VALUES("

                            for index, value in enumerate(row):

                                if value is None:
                                    insert += "NULL"

                                elif isinstance(
                                    value,
                                    (int,float,bytes,bytearray,Decimal,),):
                                    insert += str(value)

                                elif isinstance(
                                    value,
                                    (datetime,date,time,timedelta,),):
                                    insert += f"'{value}'"

                                else:
                                    insert += repr(value)

                                if index != len(row) - 1:
                                    insert += ","

                            insert += ");\n"

                            f.write(insert.encode("utf-8"))

                        if ( buffer.getbuffer().nbytes
                            >= source._single_buffer_size):
                            print(
                                f"upload part {t} on {target_file}")
                            source._upload_part(
                                body=buffer.getvalue())
                            buffer.seek(0)
                            buffer.truncate(0)
                    f.write(
                        f"UNLOCK TABLES;\n".encode("utf-8")
                    )

            #
            # CSV出力
            print(plains)
            if "csv" in plains:

                source.debug(f"parse data: {t} into .csv")

                target_file = f"data/{t}.csv"

                with zf.open(target_file, mode="w") as csv_binary:

                    text_writer = io.TextIOWrapper(
                        csv_binary,
                        encoding="utf-8",
                        newline="",
                        write_through=True,
                    )

                    writer = csv.writer(text_writer)

                    cursor = source.connection.cursor()

                    cursor.execute(f"SELECT * FROM {t}")
                    
                    # ヘッダ
                    writer.writerow(
                        [col[0] for col in cursor.description]
                    )

                    count = 0

                    while True:

                        rows = cursor.fetchmany(
                            source._config.batch_size
                        )

                        if not rows:
                            break

                        for row in rows:
                            writer.writerow(row)
                            count += 1

                        print(
                            f"{t}: {count}件出力済み"
                        )

                        # Multipart Upload
                        if (
                            buffer.getbuffer().nbytes
                            >= source._single_buffer_size
                        ):

                            source._upload_part(
                                body=buffer.getvalue()
                            )

                            buffer.seek(0)
                            buffer.truncate(0)

                    text_writer.flush()
                    cursor.close()

                    print(
                        f"{t}: 合計 {count}件 出力しました"
                    )

    #
    # 最終パート送信
    #
    if buffer.getbuffer().nbytes > 0:
        source._upload_part(
            body=buffer.getvalue()
        )

    source._complete_upload()
    source.close()