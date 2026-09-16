
# libraries
from decimal import Decimal
from datetime import datetime, date, time, timedelta
from mysql.connector import Error
import io
import zipfile
import csv
import json
# self-implementations
from backup_tool.s3_source import S3Source
import mysql.connector

import os
from dotenv import load_dotenv

def s3_multipart_upload(
    source: S3Source,
    tables: list[str],
    plains: list[str],
    sql_no_data=False,
) -> None:
    
    try:
        source.connect()
        
        buffer = io.BytesIO()
        with zipfile.ZipFile(
            buffer, mode="a",
            compression=zipfile.ZIP_DEFLATED,
        ) as zf:
            
            #tに名称を代入してるので新しくリスト
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
                        
                        for raw_iter in source.iter_row_batches(t):#保留
                            source.debug(raw_iter)
                            for it in raw_iter:#ITとは
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
            
                source.debug(f"parse table: {t} into .csv")
            
                target_file = f"data/{t}.csv"
                with zf.open(
                    target_file, mode="w"
                ) as f:
                    text_f=io.TextIOWrapper(f,encoding="utf-8",newline="")
                    writer = csv.writer(text_f)

                
                    if not sql_no_data:
            
                        for raw_iter in source.iter_row_batches(t):#保留
                            #source.debug(raw_iter)

                            for it in raw_iter:
                                writer.writerow(it)
                    
                            text_f.flush()

                            if buffer.getbuffer().nbytes >= source._single_buffer_size:
                                print(f"upload part {t} on {target_file} buffer below")
                                source._upload_part(
                                    body=buffer.getvalue(),
                                )
                                buffer.seek(0)
                
                    if buffer.getbuffer().nbytes >= source._single_buffer_size:
                        print(f"upload part {t} on {target_file} buffer below")
                        source._upload_part(
                            body=buffer.getvalue(),
                        )

            #json
            source.debug("parse manifest.json")
            
            target_file = "manifest.json"
            load_dotenv("settings.env")

            config = {
                "host": os.getenv("MYSQL_HOST"),
                "port": int(os.getenv("MYSQL_PORT")),
                "user": os.getenv("MYSQL_USER"),
                "password": os.getenv("MYSQL_PASSWORD"),
                "database": os.getenv("MYSQL_DATABASE"),
            }

            connection = mysql.connector.connect(**config)
            cursor = connection.cursor()
            cursor.execute("SELECT VERSION();")
            version = cursor.fetchone()

            manifest = {
                "tables": tables,
                "sql_files": [f"schema/{t}.sql" for t in tables],
                "csv_files": [f"data/{t}.csv" for t in tables],
                "バックアップ日時:": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "MySQL Version": "MySQL Version: "+version[0] ,
            }

            with zf.open(target_file, mode="w") as f:
                json_str = json.dumps(
                    manifest,
                    ensure_ascii=False,
                    indent=2
                )

                f.write(json_str.encode("utf-8"))   



        source._upload_part(
                body=buffer.getvalue()
                )
        
        source._complete_upload()

    except Exception as e:
        print(f"Error: {e}")
        source._abort()
        raise 

    finally:
        source.close()

       