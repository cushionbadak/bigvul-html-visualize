# thanks chatgpt

from collections import deque
from pathlib import Path
import time

import validators

from flask import Flask, render_template, request
import sqlite3



BIGVUL_DB_FILE = '../data/bigvul.db'
TABLE_NAME = 'bigvul'


column_names = []
query_history = deque(maxlen=10)


app = Flask(__name__)


def get_column_names():
    global column_names
    conn = sqlite3.connect(BIGVUL_DB_FILE)
    cursor = conn.cursor()
    cursor.execute(f'PRAGMA table_info({TABLE_NAME})')
    query_results = cursor.fetchall()
    column_names = [query_result[1] for query_result in query_results]
    conn.close()


@app.template_filter('is_url')
def is_url(s):
    return validators.url(s)


@app.template_filter('is_columnname_code_related')
def is_columnname_code_related(s):
    return s in ['func_after', 'func_before', 'patch', 'vul_func_with_fix']


@app.route('/', methods=['GET'])
def index():
    global column_names, query_history

    where_clause = request.args.get('where', "").strip()
    limit = request.args.get('limit', "1").strip()
    offset = request.args.get('offset', "0").strip()

    # Yeah it's dangerous
    SQL_QUERY = ' '.join(
        ['SELECT', '*', 'FROM', TABLE_NAME]
          + (["WHERE", where_clause] if where_clause != "" else [])
          + ["LIMIT", limit, "OFFSET", offset]
        )
    #print(SQL_QUERY)

    # set query_history
    query_history.append((where_clause, limit, offset, SQL_QUERY))
    
    # SQLite와 연결
    conn = sqlite3.connect(BIGVUL_DB_FILE)
    cursor = conn.cursor()
    # 쿼리 실행
    start_time = time.time()
    try:
        cursor.execute(SQL_QUERY)
        rows = cursor.fetchall()
        sql_error_flag = False
    except:
        rows = []
        sql_error_flag = True
    sql_time_str = "%.2f" % (time.time() - start_time)
    prepared_data = [zip(column_names, row) for row in rows]
    conn.close()
    # 웹 페이지로 데이터 전달
    return render_template(
        "index.html", 
        prepared_data=prepared_data, 
        query_history=query_history, 
        sql_error_flag=sql_error_flag, 
        sql_time_str=sql_time_str,
        previous_where=where_clause,
        previous_limit=limit,
        previous_offset=offset
        )

@app.route('/statistics')
def statistics():
    return render_template("statistics.html")

if __name__ == "__main__":
    get_column_names()
    app.run(debug=True)
