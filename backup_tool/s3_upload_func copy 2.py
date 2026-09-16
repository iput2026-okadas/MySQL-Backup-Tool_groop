
# libraries
from decimal import Decimal
from datetime import datetime, date, time, timedelta

import io
import zipfile

# self-implementations
from backup_tool.s3_source import S3Source


def s3_multipart_upload(
    source: S3Source,
    tables: list[str],
    plains: list[str],
    sql_no_data=False,
) -> None:

    source.connect()
    
    buffer = io.BytesIO()
    with zipfile.ZipFile(
        buffer, mode="a",
        compression=zipfile.ZIP_DEFLATED,
    ) as zf:
        
        
        for t in tables:
        # sql
            source.debug(f"parse table: {t} into .sql")

            target_file = f"schema/{t}.sql"
            with zf.open(
                target_file, mode="w"
            ) as f:
                            
                f.write("\n".encode("utf-8"))

                f.write(f"DROP TABLE IF EXISTS {t};\n".encode("utf-8"))
                f.write(source.get_create_table(t)[0][1].encode("utf-8"))

                f.write(f";\n".encode("utf-8"))
                f.write(f"\n".encode("utf-8"))

                source.debug(column_types := source.get_column_types(t))

                insert = ""

                if not sql_no_data:
                    f.write(f"LOCK TABLES {t} WRITE;\n".encode("utf-8"))
                    
                    for raw_iter in source.iter_row_batches(t):
                        source.debug(raw_iter)
                        for it in raw_iter:
                            insert = f"INSERT INTO {t} VALUES("

                            for index, i in enumerate(it):
                                if i == None:
                                    insert = insert + "NULL"
                                elif isinstance(i, (int, float, bytes, bytearray, Decimal)):
                                    insert = insert + str(i)
                                elif isinstance(i, (datetime, date, time, timedelta)):
                                    insert = insert + "\'" + str(i) + "\'"
                                else:
                                    insert = insert + repr(i)

                                if not index == len(it) - 1:
                                    insert = insert + ","
                            insert = insert + ");\n"

                            f.write(insert.encode("utf-8"))
                            insert = ""

                        if buffer.getbuffer().nbytes >= source._single_buffer_size:
                            print(f"upload part {t} on {target_file} buffer below")
                            source._upload_part(
                                body=buffer.getvalue(),
                            )
                            buffer.seek(0)

                f.write(f"UNLOCK TABLES;\n".encode("utf-8"))
                if buffer.getbuffer().nbytes >= source._single_buffer_size:
                    print(f"upload part {t} on {target_file} buffer below")
                    source._upload_part(
                        body=buffer.getvalue(),
                    )
                    buffer.seek(0)
                
        # csv
            if "csv" in plains:
                source.debug(f"parse data: {t} into .csv")

                target_file = f"younameit"
                with zf.open(
                    target_file, mode="w"
                ) as f:
                    # TODO csv output process for a single table
                    pass






    # last buffer uploaded here
    source._upload_part(
        body=buffer.getvalue()
    )

    source._complete_upload()
    source.close()