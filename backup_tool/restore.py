
# libraries
import zipfile
import json
import csv

import mysql.connector
from mysql.connector import MySQLConnection

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
                    "manifest.json", mode="r"
                ) as jf:
                    mnfst_json = json.load(jf)

                database_name = mnfst_json["database"]

                cursor.execute(f"show databases like \'{database_name}\';")
                is_exist = cursor.fetchall()
                if is_exist:
                    print(f"are you sure to replace the database?: {database_name}")
                    ans = ""
                    while not (ans == "y" or ans == "n"):
                        ans = input("y/n: ")
                    match ans:
                        case "y":
                            print("yes")
                        case "n":
                            print("no")
                            return None
                        case _: print("aaaaaaaaaaaaaaaaaaaaaa")

                cursor.execute(f"drop database if exists {database_name};")
                cursor.execute(f"""
create database {database_name}
    character set utf8mb4
    COLLATE utf8mb4_0900_ai_ci;
""")

                cursor.execute(f"use {database_name};")

                for table in mnfst_json["tables"]:
                    zf_sql = zf.open(f"schema/{table}.sql", mode="r")
                    cursor.execute(zf_sql.read().decode("utf-8"))

                    zf_csv = zf.open(f"data/{table}.csv", mode="r")
                    f_csv = [line.decode('utf-8') for line in zf_csv.readlines()]
                    r_csv = csv.reader(f_csv)

                    csv_lines = list(r_csv)

                    names = csv_lines.pop(0)
                    types = csv_lines.pop(0)

                    insert = f"insert into {table} ("
                    insert += f"{",".join(names)}) values "
                    csv_line = csv_lines.pop(0)
                    insert += f"({",".join(csv_line)})"
                    for csv_line in csv_lines:
                        insert += f", ({",".join(csv_line)})"
                    insert += ";"
                    cursor.execute(insert)



        else: # from local (non zip)
            with open(
                f"{rstr_from}/manifest.json",
                mode="r", encoding='utf-8'
            ) as jf:
                mnfst_json = json.load(jf)

                database_name = mnfst_json["database"]

                cursor.execute(f"show databases like \'{database_name}\';")
                is_exist = cursor.fetchall()
                if is_exist:
                    print(f"are you sure to replace the database?: {database_name}")
                    ans = ""
                    while not (ans == "y" or ans == "n"):
                        ans = input("y/n: ")
                    match ans:
                        case "y":
                            print("yes")
                        case "n":
                            print("no")
                            return None
                        case _: print("aaaaaaaaaaaaaaaaaaaaaa")

                cursor.execute(f"drop database if exists {database_name};")
                cursor.execute(f"""
create database {database_name}
    character set utf8mb4
    COLLATE utf8mb4_0900_ai_ci;
""")

                cursor.execute(f"use {database_name};")

                for table in mnfst_json["tables"]:
                    sql = open(f"{rstr_from}/schema/{table}.sql", mode="r", encoding="utf-8")

                    cursor.execute(sql.read())

                    f_csv = open(f"{rstr_from}/data/{table}.csv", mode="r", encoding="utf-8")
                    r_csv = csv.reader(f_csv)

                    csv_lines = list(r_csv)

                    names = csv_lines.pop(0)
                    types = csv_lines.pop(0)

                    insert = f"insert into {table} ("
                    insert += f"{",".join(names)}) values "
                    csv_line = csv_lines.pop(0)
                    insert += f"({",".join(csv_line)})"
                    for csv_line in csv_lines:
                        insert += f", ({",".join(csv_line)})"
                    insert += ";"
                    cursor.execute(insert)



        connection.commit()
    except Exception as e:
        print(e)

    finally:

        cursor.close()
        connection.close()