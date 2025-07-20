import streamlit as st
import pandas as pd
import os
from datetime import date
from streamlit_calendar import calendar

# --- ファイル定義 ---
BOOKS_CSV = "books.csv"
LOGS_CSV = "logs.csv"

def load_books():
    if os.path.exists(BOOKS_CSV):
        return pd.read_csv(BOOKS_CSV)
    else:
        return pd.DataFrame(columns=["title", "total_pages", "author", "publisher", "purchase_date", "start_date", "current_page", "status", "finish_date"])

def save_books(df):
    df.to_csv(BOOKS_CSV, index=False)

def load_logs():
    if os.path.exists(LOGS_CSV):
        return pd.read_csv(LOGS_CSV, parse_dates=["date"])
    else:
        return pd.DataFrame(columns=["date", "title", "pages"])

def save_logs(df):
    df.to_csv(LOGS_CSV, index=False)

books = load_books()
if "status" not in books.columns:
    books["status"] = "reading"
if "finish_date" not in books.columns:
    books["finish_date"] = ""

st.title("📚 読書トラッカー")

if "show_message" not in st.session_state:
    st.session_state["show_message"] = ""

if st.session_state["show_message"]:
    st.success(st.session_state["show_message"])
    st.session_state["show_message"] = ""

# ---- 新規本登録 ----
title = st.text_input("本のタイトル", key="title")
total_pages = st.number_input("総ページ数", min_value=1, step=1, key="total_pages")
author = st.text_input("著者名", key="author")
publisher = st.text_input("出版社名", key="publisher")

set_purchase = st.checkbox("購入日を入力する", key="set_purchase", value=False)
if set_purchase:
    purchase_date = st.date_input("購入日", key="purchase_date")
else:
    purchase_date = ""

set_start = st.checkbox("読書開始日を入力する", key="set_start", value=False)
if set_start:
    start_date = st.date_input("読書開始日", key="start_date")
else:
    start_date = ""

if st.button("本を追加する"):
    if not title or not total_pages:
        st.error("本のタイトルと総ページ数は必須です！")
    else:
        new_book = pd.DataFrame([{
            "title": title,
            "total_pages": total_pages,
            "author": author,
            "publisher": publisher,
            "purchase_date": purchase_date if purchase_date else "",
            "start_date": start_date if start_date else "",
            "current_page": 0,
            "status": "reading",
            "finish_date": ""
        }])
        books = pd.concat([books, new_book], ignore_index=True)
        save_books(books)
        st.session_state["show_message"] = f"「{title}」を追加しました！"
        st.rerun()

# ---- 読書中・読了本の分割 ----
reading_books = books[books["status"] != "done"].reset_index(drop=True)
finished_books = books[books["status"] == "done"].reset_index(drop=True)

num_finished = len(finished_books)
st.markdown(f"**読了冊数：{num_finished}冊**")

# ---- 読書中の本一覧 ----
st.header("📖 読書中の本一覧")
if reading_books.empty:
    st.info("読書中の本はありません。")
else:
    if "edit_idx" not in st.session_state:
        st.session_state["edit_idx"] = None
    if "edit_purchase_date" not in st.session_state:
        st.session_state["edit_purchase_date"] = {}
    if "edit_start_date" not in st.session_state:
        st.session_state["edit_start_date"] = {}

    for idx, row in reading_books.iterrows():
        st.subheader(f"{row['title']}（{row['current_page']} / {row['total_pages']}ページ）")
        progress = row['current_page'] / row['total_pages']
        st.progress(progress)

        if st.session_state["edit_idx"] == idx:
            st.info("編集中")
            edit_title = st.text_input("タイトル", value=row['title'], key=f"edit_title_{idx}")
            edit_total_pages = st.number_input("総ページ数", min_value=1, step=1, value=int(row['total_pages']), key=f"edit_total_{idx}")
            edit_author = st.text_input("著者名", value=row['author'], key=f"edit_author_{idx}")
            edit_publisher = st.text_input("出版社名", value=row['publisher'], key=f"edit_pub_{idx}")

            # 購入日
            if idx not in st.session_state["edit_purchase_date"]:
                has_purchase = not pd.isna(row['purchase_date']) and str(row['purchase_date']).strip() != "" and str(row['purchase_date']).strip().lower() != "nan"
                st.session_state["edit_purchase_date"][idx] = has_purchase
            set_purchase = st.checkbox("購入日を入力する", key=f"edit_set_purchase_{idx}", value=st.session_state["edit_purchase_date"][idx])
            purchase_date_val = ""
            if set_purchase:
                if not pd.isna(row['purchase_date']) and str(row['purchase_date']).strip() != "" and str(row['purchase_date']).strip().lower() != "nan":
                    try:
                        default_purchase = pd.to_datetime(row['purchase_date'], format="mixed").date()
                    except:
                        default_purchase = None
                else:
                    default_purchase = None
                purchase_date_val = st.date_input("購入日", key=f"edit_purchase_{idx}", value=default_purchase if default_purchase else date.today())
            else:
                purchase_date_val = ""

            # 読書開始日
            if idx not in st.session_state["edit_start_date"]:
                has_start = not pd.isna(row['start_date']) and str(row['start_date']).strip() != "" and str(row['start_date']).strip().lower() != "nan"
                st.session_state["edit_start_date"][idx] = has_start
            set_start = st.checkbox("読書開始日を入力する", key=f"edit_set_start_{idx}", value=st.session_state["edit_start_date"][idx])
            start_date_val = ""
            if set_start:
                if not pd.isna(row['start_date']) and str(row['start_date']).strip() != "" and str(row['start_date']).strip().lower() != "nan":
                    try:
                        default_start = pd.to_datetime(row['start_date'], format="mixed").date()
                    except:
                        default_start = None
                else:
                    default_start = None
                start_date_val = st.date_input("読書開始日", key=f"edit_start_{idx}", value=default_start if default_start else date.today())
            else:
                start_date_val = ""

            save_col, cancel_col = st.columns(2)
            with save_col:
                if st.button("保存", key=f"save_edit_{idx}"):
                    books_idx = reading_books.index[idx]
                    books.at[books_idx, 'title'] = edit_title
                    books.at[books_idx, 'total_pages'] = edit_total_pages
                    books.at[books_idx, 'author'] = edit_author
                    books.at[books_idx, 'publisher'] = edit_publisher
                    books.at[books_idx, 'purchase_date'] = purchase_date_val if set_purchase else ""
                    books.at[books_idx, 'start_date'] = start_date_val if set_start else ""
                    save_books(books)
                    st.session_state["show_message"] = "保存しました。"
                    st.session_state["edit_idx"] = None
                    st.rerun()
            with cancel_col:
                if st.button("キャンセル", key=f"cancel_edit_{idx}"):
                    st.session_state["edit_idx"] = None
                    st.rerun()
        else:
            col1, col2 = st.columns([3, 1])
            with col1:
                new_page = st.number_input(
                    "現在のページ",
                    min_value=0, max_value=int(row['total_pages']),
                    value=int(row['current_page']),
                    step=1, key=f"page_{idx}"
                )
                progress_date = st.date_input(
                    "日付", value=date.today(), key=f"progress_date_{idx}"
                )
                if st.button(f"{row['title']} の進捗を更新", key=f"update_{idx}"):
                    books_idx = reading_books.index[idx]
                    logs = load_logs()
                    # 日付カラム型変換（比較エラー防止）
                    if logs.shape[0] > 0:
                        logs["date"] = pd.to_datetime(logs["date"], format="mixed").dt.date
                    # 普通にdelta分だけログ追加
                    delta = new_page - int(row['current_page'])
                    books.at[books_idx, 'current_page'] = new_page
                    if new_page == int(row['total_pages']):
                        books.at[books_idx, "status"] = "done"
                        if not books.at[books_idx, "finish_date"]:
                            books.at[books_idx, "finish_date"] = str(progress_date)
                        st.session_state["show_message"] = f"「{row['title']}」を読了しました！"
                    save_books(books)
                    if delta > 0:
                        new_log = pd.DataFrame([{
                            "date": progress_date,
                            "title": row['title'],
                            "pages": delta
                        }])
                        logs = pd.concat([logs, new_log], ignore_index=True)
                        save_logs(logs)
                    st.session_state["show_message"] = f"{row['title']} の進捗を{new_page}ページ（{progress_date}付）に更新しました！"
                    st.rerun()
            with col2:
                b1, b2 = st.columns(2)
                with b1:
                    if st.button("編集", key=f"edit_{idx}"):
                        st.session_state["edit_idx"] = idx
                        st.rerun()
                with b2:
                    if st.button("削除", key=f"delete_{idx}"):
                        books_idx = reading_books.index[idx]
                        # logsも削除
                        logs = load_logs()
                        logs = logs[logs["title"] != row['title']]
                        save_logs(logs)
                        books = books.drop(books_idx).reset_index(drop=True)
                        save_books(books)
                        st.session_state["show_message"] = f"「{row['title']}」とその読書記録を削除しました。"
                        st.rerun()
        st.write("---")

    st.markdown(f"**読書中の累計読書ページ数：{reading_books['current_page'].sum()}ページ**")

# ---- 読了した本一覧（編集・戻す一切なし）----
st.header("📚 読了した本一覧")
def show_value(x):
    return "未入力" if pd.isna(x) or str(x).strip() == "" else str(x)

if finished_books.empty:
    st.info("まだ読了した本はありません。")
else:
    for idx, row in finished_books.iterrows():
        st.subheader(f"{row['title']}（全{row['total_pages']}ページ）")
        st.markdown(
            f"- 著者：{show_value(row['author'])}"
            f"\n- 出版社：{show_value(row['publisher'])}"
            f"\n- 購入日：{show_value(row['purchase_date'])}"
            f"\n- 読書開始日：{show_value(row['start_date'])}"
            f"\n- 読了日：{show_value(row['finish_date'])}"
        )
        st.write("---")

    st.markdown(f"**読了した累計ページ数：{finished_books['current_page'].sum()}ページ**")

# ---- カレンダー表示 ----
logs = load_logs()
if not logs.empty:
    logs["date"] = pd.to_datetime(logs["date"], format="mixed").dt.date
    logs_day = logs.groupby("date")["pages"].sum().reset_index()
    events = []
    for _, r in logs_day.iterrows():
        events.append({
            "title": f"{r['pages']}ページ",
            "start": str(r["date"]),
            "end": str(r["date"]),
            "allDay": True
        })
    st.subheader("📅 読書カレンダー（日ごとの読書ページ数）")
    calendar_options = {
        "initialView": "dayGridMonth",
        "events": events,
        "height": 650,
    }
    calendar(calendar_options, key="read_calendar")
else:
    st.info("まだ読書ログがありません。進捗を記録するとカレンダーが表示されます。")
