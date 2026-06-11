import streamlit as st
import sqlite3
import calendar
from datetime import date, datetime
import os

# ──────────────────────────────────────────────
# 기본 설정
# ──────────────────────────────────────────────
st.set_page_config(page_title="팀 공유 일정 달력", page_icon="📅", layout="wide")

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "team_calendar.db")

# 팀장 / 인력 정의
TEAM_LEADERS = ["서유석", "홍영태", "김수용"]
WORKERS = ["김만두", "박순일", "고한명", "서범석"]

# 인원수 색상 (필요 인력이 많을수록 강조)
def count_color(n):
    if n <= 1:
        return "#2e7d32"   # 초록
    elif n == 2:
        return "#ef6c00"   # 주황
    else:
        return "#c62828"   # 빨강


# ──────────────────────────────────────────────
# DB 초기화 / 함수
# ──────────────────────────────────────────────
def get_conn():
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    return conn


def init_db():
    conn = get_conn()
    c = conn.cursor()
    # 작업 일정
    c.execute("""
        CREATE TABLE IF NOT EXISTS tasks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            work_date TEXT NOT NULL,
            leader TEXT NOT NULL,
            task TEXT NOT NULL,
            num_people INTEGER NOT NULL,
            workers TEXT,
            created_at TEXT
        )
    """)
    # 메모 (팀간 소통)
    c.execute("""
        CREATE TABLE IF NOT EXISTS memos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            work_date TEXT NOT NULL,
            author TEXT NOT NULL,
            content TEXT NOT NULL,
            created_at TEXT
        )
    """)
    conn.commit()
    conn.close()


def add_task(work_date, leader, task, num_people, workers):
    conn = get_conn()
    c = conn.cursor()
    c.execute(
        "INSERT INTO tasks (work_date, leader, task, num_people, workers, created_at) VALUES (?,?,?,?,?,?)",
        (work_date, leader, task, num_people, ",".join(workers),
         datetime.now().strftime("%Y-%m-%d %H:%M")),
    )
    conn.commit()
    conn.close()


def get_tasks_by_date(work_date):
    conn = get_conn()
    c = conn.cursor()
    c.execute("SELECT id, leader, task, num_people, workers FROM tasks WHERE work_date=? ORDER BY id",
              (work_date,))
    rows = c.fetchall()
    conn.close()
    return rows


def get_tasks_for_month(year, month):
    conn = get_conn()
    c = conn.cursor()
    prefix = f"{year:04d}-{month:02d}-"
    c.execute("SELECT work_date, leader, task, num_people, workers FROM tasks WHERE work_date LIKE ? ORDER BY id",
              (prefix + "%",))
    rows = c.fetchall()
    conn.close()
    result = {}
    for wd, leader, task, num, workers in rows:
        result.setdefault(wd, []).append((leader, task, num, workers))
    return result


def delete_task(task_id):
    conn = get_conn()
    c = conn.cursor()
    c.execute("DELETE FROM tasks WHERE id=?", (task_id,))
    conn.commit()
    conn.close()


def add_memo(work_date, author, content):
    conn = get_conn()
    c = conn.cursor()
    c.execute(
        "INSERT INTO memos (work_date, author, content, created_at) VALUES (?,?,?,?)",
        (work_date, author, content, datetime.now().strftime("%Y-%m-%d %H:%M")),
    )
    conn.commit()
    conn.close()


def get_memos_by_date(work_date):
    conn = get_conn()
    c = conn.cursor()
    c.execute("SELECT id, author, content, created_at FROM memos WHERE work_date=? ORDER BY id",
              (work_date,))
    rows = c.fetchall()
    conn.close()
    return rows


def delete_memo(memo_id):
    conn = get_conn()
    c = conn.cursor()
    c.execute("DELETE FROM memos WHERE id=?", (memo_id,))
    conn.commit()
    conn.close()


init_db()

# ──────────────────────────────────────────────
# 세션 상태
# ──────────────────────────────────────────────
if "user" not in st.session_state:
    st.session_state.user = None
if "view_year" not in st.session_state:
    st.session_state.view_year = date.today().year
if "view_month" not in st.session_state:
    st.session_state.view_month = date.today().month
if "selected_date" not in st.session_state:
    st.session_state.selected_date = None


# ──────────────────────────────────────────────
# 간단 로그인 (이름 선택)
# ──────────────────────────────────────────────
def login_screen():
    st.title("📅 팀 공유 일정 달력")
    st.markdown("#### 로그인 — 본인 이름을 선택하세요")
    all_names = TEAM_LEADERS + WORKERS
    cols = st.columns(len(all_names))
    for i, name in enumerate(all_names):
        role = "팀장" if name in TEAM_LEADERS else "인력"
        if cols[i].button(f"{name}\n({role})", use_container_width=True, key=f"login_{name}"):
            st.session_state.user = name
            st.rerun()


if st.session_state.user is None:
    login_screen()
    st.stop()


# ──────────────────────────────────────────────
# 상단 헤더
# ──────────────────────────────────────────────
top_l, top_r = st.columns([4, 1])
with top_l:
    role = "팀장" if st.session_state.user in TEAM_LEADERS else "인력"
    st.markdown(f"### 📅 팀 공유 일정 달력  ·  **{st.session_state.user}** ({role}) 님")
with top_r:
    if st.button("로그아웃", use_container_width=True):
        st.session_state.user = None
        st.rerun()

st.divider()

# ──────────────────────────────────────────────
# 월 네비게이션
# ──────────────────────────────────────────────
nav_l, nav_c, nav_r = st.columns([1, 2, 1])
with nav_l:
    if st.button("◀ 이전 달", use_container_width=True):
        st.session_state.view_month -= 1
        if st.session_state.view_month < 1:
            st.session_state.view_month = 12
            st.session_state.view_year -= 1
        st.rerun()
with nav_c:
    st.markdown(
        f"<h3 style='text-align:center;margin:0;'>{st.session_state.view_year}년 {st.session_state.view_month}월</h3>",
        unsafe_allow_html=True)
with nav_r:
    if st.button("다음 달 ▶", use_container_width=True):
        st.session_state.view_month += 1
        if st.session_state.view_month > 12:
            st.session_state.view_month = 1
            st.session_state.view_year += 1
        st.rerun()

st.write("")

# ──────────────────────────────────────────────
# 달력 렌더링
# ──────────────────────────────────────────────
year = st.session_state.view_year
month = st.session_state.view_month
month_tasks = get_tasks_for_month(year, month)

weekday_names = ["월", "화", "수", "목", "금", "토", "일"]
header_cols = st.columns(7)
for i, wn in enumerate(weekday_names):
    color = "#c62828" if i == 6 else ("#1565c0" if i == 5 else "#333")
    header_cols[i].markdown(
        f"<div style='text-align:center;font-weight:700;color:{color};'>{wn}</div>",
        unsafe_allow_html=True)

cal = calendar.Calendar(firstweekday=0)  # 월요일 시작
weeks = cal.monthdayscalendar(year, month)
today = date.today()

for week in weeks:
    cols = st.columns(7)
    for i, day in enumerate(week):
        with cols[i]:
            if day == 0:
                st.markdown("&nbsp;", unsafe_allow_html=True)
                continue

            wd_str = f"{year:04d}-{month:02d}-{day:02d}"
            tasks = month_tasks.get(wd_str, [])
            is_today = (today.year == year and today.month == month and today.day == day)

            # 날짜 박스 내용 구성
            day_color = "#c62828" if i == 6 else ("#1565c0" if i == 5 else "#222")
            day_label = f"**{day}**"
            border = "2px solid #1565c0" if is_today else "1px solid #ddd"
            bg = "#e3f2fd" if is_today else "#fafafa"

            # 작업 내용 미리보기 HTML (한 화면에 다 보이도록 줄바꿈)
            inner = ""
            for leader, task, num, workers in tasks:
                c = count_color(num)
                w_txt = workers if workers else ""
                inner += (
                    f"<div style='background:#fff;border-left:4px solid {c};"
                    f"border-radius:4px;padding:4px 6px;margin:3px 0;font-size:11px;line-height:1.35;'>"
                    f"<b>{leader}</b><br>{task}<br>"
                    f"<span style='color:{c};font-weight:700;'>{num}명</span>"
                    f"{('('+w_txt+')') if w_txt else ''}"
                    f"</div>"
                )

            st.markdown(
                f"<div style='border:{border};border-radius:8px;background:{bg};"
                f"padding:6px;min-height:90px;'>"
                f"<div style='color:{day_color};font-weight:700;font-size:14px;'>{day}</div>"
                f"{inner}</div>",
                unsafe_allow_html=True)

            if st.button("열기", key=f"open_{wd_str}", use_container_width=True):
                st.session_state.selected_date = wd_str
                st.rerun()

st.divider()

# ──────────────────────────────────────────────
# 선택된 날짜 상세 (작업 입력 / 메모)
# ──────────────────────────────────────────────
if st.session_state.selected_date:
    sel = st.session_state.selected_date
    st.markdown(f"## 🗓️ {sel} 상세")

    left, right = st.columns(2)

    # ── 작업 일정 ──
    with left:
        st.markdown("### 📋 작업 일정")
        existing = get_tasks_by_date(sel)
        if existing:
            for tid, leader, task, num, workers in existing:
                c = count_color(num)
                w_txt = f"({workers})" if workers else ""
                box, btn = st.columns([5, 1])
                box.markdown(
                    f"<div style='background:#fff;border-left:5px solid {c};"
                    f"border-radius:6px;padding:10px 12px;margin:4px 0;'>"
                    f"<div style='font-size:16px;font-weight:700;'>{leader}</div>"
                    f"<div style='font-size:15px;margin:2px 0;'>{task}</div>"
                    f"<div style='font-size:15px;color:{c};font-weight:700;'>{num}명{w_txt}</div>"
                    f"</div>",
                    unsafe_allow_html=True)
                if btn.button("🗑", key=f"deltask_{tid}"):
                    delete_task(tid)
                    st.rerun()
        else:
            st.info("등록된 작업이 없습니다.")

        st.markdown("#### ➕ 작업 추가")
        leader_sel = st.selectbox("팀장 선택", TEAM_LEADERS, key="leader_sel")
        task_input = st.text_input("작업 내용", placeholder="예) 국민연금 추가작업", key="task_input")
        num_sel = st.number_input("필요 인력 수", min_value=1, max_value=4, value=1, step=1, key="num_sel")
        worker_sel = st.multiselect("투입 인력 (선택)", WORKERS, key="worker_sel")

        if st.button("작업 등록", type="primary", use_container_width=True):
            if task_input.strip():
                add_task(sel, leader_sel, task_input.strip(), int(num_sel), worker_sel)
                st.success("등록되었습니다.")
                st.rerun()
            else:
                st.warning("작업 내용을 입력하세요.")

    # ── 메모 (팀간 소통) ──
    with right:
        st.markdown("### 💬 메모 (팀간 소통)")
        memos = get_memos_by_date(sel)
        if memos:
            for mid, author, content, created in memos:
                box, btn = st.columns([6, 1])
                box.markdown(
                    f"<div style='background:#fff8e1;border-radius:6px;"
                    f"padding:8px 12px;margin:4px 0;'>"
                    f"<b>{author}</b> "
                    f"<span style='color:#999;font-size:11px;'>{created}</span><br>"
                    f"{content}</div>",
                    unsafe_allow_html=True)
                if btn.button("🗑", key=f"delmemo_{mid}"):
                    delete_memo(mid)
                    st.rerun()
        else:
            st.info("메모가 없습니다.")

        st.markdown("#### ✏️ 메모 작성")
        memo_input = st.text_area("내용", placeholder="다른 팀에게 남길 말을 적으세요.", key="memo_input")
        if st.button("메모 남기기", use_container_width=True):
            if memo_input.strip():
                add_memo(sel, st.session_state.user, memo_input.strip())
                st.success("메모가 등록되었습니다.")
                st.rerun()
            else:
                st.warning("내용을 입력하세요.")

    if st.button("닫기", use_container_width=True):
        st.session_state.selected_date = None
        st.rerun()
else:
    st.info("달력에서 날짜의 **열기** 버튼을 누르면 작업 입력과 메모를 작성할 수 있습니다.")
