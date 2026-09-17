
# libraries
import zipfile
from zipfile import ZipFile
import json
import csv

from collections import deque

import mysql.connector
from mysql.connector import MySQLConnection

from multiprocessing import Pool, cpu_count


# self-implementations
from backup_tool.config import MySQLConfig



def restore_from_manifest(
    rstr_from: str,
    mysql_config: MySQLConfig,
) -> None:

    
    try:
        connection = mysql.connector.connect(
            host=mysql_config.host,
            port=mysql_config.port,
            user=mysql_config.user,
            password=mysql_config.password,
            database=mysql_config.database,
            charset="utf8mb4",
            use_unicode=True,
            autocommit=True,
        )

        cursor = connection.cursor()


        mnfst_json = dict()
        database_name = ""

    # heiii, plz let me integrate zip and non zip process
    # why cant they be considered as the same instance
    # it makes me code em indivisually, gimme a break :(
    # ohhhh dizzy
        is_zip = rstr_from.endswith(".zip")

        if is_zip: # from local zip
            with zipfile.ZipFile(
                rstr_from, mode="r"
            ) as zf:
                with zf.open(
                    "test.json", mode="r"
                ) as jf:
                    mnfst_json = json.load(jf)

                database_name = mnfst_json["database"]

                cursor.execute(f"show databases like \'{database_name}\';")
                is_exist = cursor.fetchall()
                if is_exist:
                    print(f"you wanna replace or add data?: into")
                    ans = ""
                    while not (ans == "r" or ans == "a"):
                        ans = input("r/a: ")
                    match ans:
                        case "r":
                            print("replacing")
                            cursor.execute(f"drop database if exists {database_name};")
                            cursor.execute(f"""
create database {database_name}
    character set utf8mb4
    COLLATE utf8mb4_0900_ai_ci;
""")
                        case "a":
                            print("adding")
                        case _: print("aaaaaaaaaaaaaaaaaaaaaa")


                connection.commit()
                cursor.close()
                connection.close()

                for table in mnfst_json["tables"]:
                    restore_4_single_table_zip(
                        mysql_config=mysql_config,
                        database_name=database_name,
                        table=table,
                        zf=zf
                    )



        else: # from local (non zip)
            with open(
                f"{rstr_from}/test.json",
                mode="r", encoding='utf-8'
            ) as jf:
                mnfst_json = json.load(jf)

                database_name = mnfst_json["database"]

                cursor.execute(f"show databases like \'{database_name}\';")
                is_exist = cursor.fetchall()
                if is_exist:
                    print(f"you wanna replace or add data?: into")
                    ans = ""
                    while not (ans == "r" or ans == "a"):
                        ans = input("r/a: ")
                    match ans:
                        case "r":
                            print("replacing")
                            cursor.execute(f"drop database if exists {database_name};")
                            cursor.execute(f"""
create database {database_name}
    character set utf8mb4
    COLLATE utf8mb4_0900_ai_ci;
""")
                        case "a":
                            print("adding")
                        case _: print("aaaaaaaaaaaaaaaaaaaaaa")

                connection.commit()
                cursor.close()
                connection.close()

                args = [(
                    mysql_config,
                    rstr_from,
                    database_name,
                    t,
                ) for t in mnfst_json["tables"]]
                n = cpu_count()
                with Pool(processes=n) as p:
                    p.starmap(restore_4_single_table, args)
                    
    except Exception as e:
        print(e)

def restore_4_single_table(
    mysql_config: MySQLConfig,
    rstr_from: str,
    database_name: str,
    table: str,
) -> None:
    print(f"restoring a table: {table}")

    connection = mysql.connector.connect(
        host=mysql_config.host,
        port=mysql_config.port,
        user=mysql_config.user,
        password=mysql_config.password,
        database=mysql_config.database,
        charset="utf8mb4",
        use_unicode=True,
        autocommit=False,
    )
    cursor = connection.cursor()
    cursor.execute(f"use {database_name};")

    sql = open(f"{rstr_from}/schema/{table}.sql", mode="r", encoding="utf-8")
    cursor.execute(sql.read())

    f_csv = open(f"{rstr_from}/data/{table}.csv", mode="r", encoding="utf-8")
    r_csv = csv.reader(f_csv)
    csv_list = list(r_csv)
    csv_lines = deque(csv_list)

    names = csv_lines.popleft()
    types = csv_lines.popleft()

    insert = f"insert into {table} ("
    insert += f"{",".join(names)}) values "
    csv_line = csv_lines.popleft()
    insert += f"({",".join(csv_line)})"
    count = 1
    while csv_lines:
        csv_line = csv_lines.popleft()
        insert += f", ({",".join(csv_line)})"
        count += 1
        if count % 777 == 0:
            if len(insert.encode("utf-8")) >= 10 * 1024 * 1024:
                insert += ";"
                cursor.execute(insert)
                insert = f"insert into {table} ("
                insert += f"{",".join(names)}) values "
                csv_line = csv_lines.popleft()
                insert += f"({",".join(csv_line)})"
            count = 1

    insert += ";"
    cursor.execute(insert)
    connection.commit()

    cursor.close()
    connection.close()

        
def restore_4_single_table_zip(
    mysql_config: MySQLConfig,
    database_name: str,
    table: str,
    zf: ZipFile
) -> None:
    print(f"restoring a table: {table}")

    connection = mysql.connector.connect(
        host=mysql_config.host,
        port=mysql_config.port,
        user=mysql_config.user,
        password=mysql_config.password,
        database=mysql_config.database,
        charset="utf8mb4",
        use_unicode=True,
        autocommit=False,
    )
    cursor = connection.cursor()
    cursor.execute(f"use {database_name};")

    zf_sql = zf.open(f"schema/{table}.sql", mode="r")
    cursor.execute(zf_sql.read().decode("utf-8"))

    zf_csv = zf.open(f"data/{table}.csv", mode="r")
    f_csv = [line.decode('utf-8') for line in zf_csv.readlines()]
    r_csv = csv.reader(f_csv)

    csv_list = list(r_csv)
    csv_lines = deque(csv_list)

    names = csv_lines.popleft()
    types = csv_lines.popleft()

    insert = f"insert into {table} ("
    insert += f"{",".join(names)}) values "
    csv_line = csv_lines.popleft()
    insert += f"({",".join(csv_line)})"
    count = 1
    while csv_lines:
        csv_line = csv_lines.popleft()
        insert += f", ({",".join(csv_line)})"
        count += 1
        if count % 777 == 0:
            if len(insert.encode("utf-8")) >= 10 * 1024 * 1024:
                insert += ";"
                cursor.execute(insert)
                insert = f"insert into {table} ("
                insert += f"{",".join(names)}) values "
                csv_line = csv_lines.popleft()
                insert += f"({",".join(csv_line)})"
            count = 1

    insert += ";"
    cursor.execute(insert)
    connection.commit()

    cursor.close()
    connection.close()