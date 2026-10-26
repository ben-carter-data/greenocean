"""Pagination and comparisons checked against a small independent database."""
import sqlite3
from pathlib import Path
import pandas as pd
import pytest

@pytest.fixture
def database(tmp_path):
    path = tmp_path/'prices.db'
    c=sqlite3.connect(path)
    c.executescript((Path(__file__).parents[1]/'etl/schema.sql').read_text())
    c.execute("INSERT INTO dim_product VALUES(1,'Frutas','Manzana','Gala','Primera')")
    c.executemany('INSERT INTO dim_region VALUES(?,?)',[(1,'Norte'),(2,'Sur')])
    c.executemany('INSERT INTO dim_channel VALUES(?,?,?)',[(1,'Mayorista','wholesale'),(2,'Feria','consumer')])
    for i,week in enumerate(pd.date_range('2026-01-05',periods=12,freq='7D')):
        for region in [1,2]:
            for channel in [1,2]:
                c.execute('INSERT INTO weekly_price VALUES(?,?,?,?,?,?,?,?,?)',
                          (week.strftime('%Y-%m-%d'),1,region,channel,'kilo',100+i*10+channel*10, None,3,None))
    c.execute("INSERT INTO weekly_price VALUES('2026-04-06',1,1,2,'unidad',NULL,NULL,1,'UNIDAD_NO_CONVERTIBLE')")
    c.commit();c.close();return path
