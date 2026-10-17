"""Pagination and comparisons checked against a small independent database."""
import sqlite3
from pathlib import Path
import pandas as pd
import pytest
from bi import data_browser as explorer

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

def test_filter_sort_and_paging_cover_every_record_once(database):
    ids=[]
    for p in range(4):
        frame,total,actual=explorer.read_page(explorer.MODES[0],{'region':'Norte'},size=8,page=p,database_file=database)
        assert total==25
        ids += frame.record_id.tolist()
    assert len(ids)==len(set(ids))==25
    frame,n,_=explorer.read_page(explorer.MODES[0],{'product':"' OR 1=1 --"},database_file=database)
    assert n==0 and frame.empty
    with pytest.raises(ValueError):
        explorer.read_page(explorer.MODES[0],sort='price; DELETE',database_file=database)
    frame,n,page=explorer.read_page(explorer.MODES[0],page=999,size=100,database_file=database)
    assert page==0 and n==49

def test_exact_previous_week_and_gap_grain(database):
    frame,n,_=explorer.read_page(explorer.MODES[1],{'region':'Norte','channel':'Feria'},start='2026-01-12',end='2026-01-12',database_file=database)
    row=frame.iloc[0]
    assert n==1 and row.price==130 and row.previous_price==120
    assert row.variation==pytest.approx((130/120-1)*100)
    missing,_,_=explorer.read_page(explorer.MODES[1],start='2026-04-06',database_file=database)
    assert missing.previous_price.isna().all() and missing.variation.isna().all()
    gaps,n,_=explorer.read_page(explorer.MODES[2],{'region':'Norte'},start='2026-01-05',end='2026-01-05',database_file=database)
    assert n==1 and gaps.iloc[0].wholesale_price==110 and gaps.iloc[0].consumer_price==120
    assert gaps.iloc[0].margin==pytest.approx(10/110)
