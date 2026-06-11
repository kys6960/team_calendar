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

# 팀장 / 팀원 정의
TEAM_LEADERS = ["서유석", "홍영태", "김수용"]
WORKERS = ["김만두", "박순일", "고한명", "서범석"]


# 인원수 색상 (필요 팀원이 많을수록 강조) - 다크 배경용 밝은 색
def count_color(n):
    if n <= 1:
        return "#66bb6a"   # 밝은 초록
    elif n == 2:
        return "#ffa726"   # 밝은 주황
    else:
        return "#ef5350"   # 밝은 빨강


# ──────────────────────────────────────────────
# 전역 다크 테마 / 달력 스타일
# ──────────────────────────────────────────────
st.markdown("""
<style>
/* 전체 배경 다크 */
.stApp { background-color: #0e1117; }

/* ── 달력 그리드 (모바일에서도 7칸 고정) ── */
.cal-grid {
    display: grid;
    grid-template-columns: repeat(7, 1fr);
    gap: 4px;
    width: 100%;
}
.cal-head {
    text-align: center;
    font-weight: 700;
    padding: 6px 0;
    font-size: 13px;
}
.cal-cell {
    display: block;
    min-height: 110px;
    background-color: #1a1f2b;
    border: 1px solid #2a3142;
    border-radius: 10px;
    padding: 6px 6px;
    text-decoration: none;
    color: #e6e6e6;
    overflow: hidden;
    transition: all 0.12s ease-in-out;
}
.cal-cell:hover {
    background-color: #232a3a;
    border-color: #4a90e2;
}
.cal-cell.empty {
    background: transparent;
    border: none;
    pointer-events: none;
}
.cal-cell.today {
    border: 2px solid #4a90e2;
    background-color: #18223a;
}
.cal-daynum {
    font-weight: 700;
    font-size: 14px;
    margin-bottom: 2px;
}
.cal-task {
    border-top: 1px solid #2a3142;
    margin-top: 4px;
    padding-top: 3px;
    font-size: 11px;
    line-height: 1.35;
    word-break: break-all;
}
.cal-task .lead { font-weight: 700; color: #ffffff; }
.cal-task .desc { color: #d0d0d0; }
@media (max-width: 640px) {
    .cal-cell { min-height: 80px; padding: 4px; }
    .cal-daynum { font-size: 12px; }
    .cal-task { font-size: 9px; }
    .cal-head { font-size: 11px; }
}
</style>
""", unsafe_allow_html=True)


# ──────────────────────────────────────────────
# DB 초기화 / 함수
# ──────────────────────────────────────────────
def get_conn():
    return sqlite3.connect(DB_PATH, check_same_thread=False)


def init_db():
    conn = get_conn()
    c = conn.cursor()
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

_qp = st.query_params

# 로그인 상태를 URL(?u=이름)에서 복원 — URL이 바뀌어도 로그인 유지
ALL_NAMES = TEAM_LEADERS + WORKERS
if st.session_state.user is None and _qp.get("u") in ALL_NAMES:
    st.session_state.user = _qp.get("u")

# 클릭된 날짜(?d=YYYY-MM-DD) 처리
if _qp.get("d"):
    st.session_state.selected_date = _qp.get("d")
    # 날짜 파라미터만 제거하고 로그인(u)은 유지
    if "d" in _qp:
        del _qp["d"]


# ──────────────────────────────────────────────
# 간단 로그인 (이름 선택)
# ──────────────────────────────────────────────
def login_screen():
    st.markdown(
        "<div style='white-space:nowrap;font-weight:800;color:#e6e6e6;"
        "font-size:clamp(20px,6vw,40px);margin:8px 0 4px 0;'>"
        "📅 팀 공유 일정 달력</div>",
        unsafe_allow_html=True)
    st.markdown("#### 로그인 — 본인 이름을 선택하세요")
    all_names = TEAM_LEADERS + WORKERS
    cols = st.columns(len(all_names))
    for i, name in enumerate(all_names):
        role = "팀장" if name in TEAM_LEADERS else "팀원"
        if cols[i].button(f"{name}\n({role})", use_container_width=True, key=f"login_{name}"):
            st.session_state.user = name
            st.query_params["u"] = name   # URL에 로그인 정보 유지
            st.rerun()


if st.session_state.user is None:
    login_screen()
    st.stop()


# ──────────────────────────────────────────────
# 상단 헤더
# ──────────────────────────────────────────────
top_l, top_r = st.columns([4, 1])
with top_l:
    role = "팀장" if st.session_state.user in TEAM_LEADERS else "팀원"
    st.markdown(
        f"<div style='font-weight:800;color:#e6e6e6;font-size:clamp(15px,4.2vw,24px);'>"
        f"<span style='white-space:nowrap;'>📅 팀 공유 일정 달력</span><br>"
        f"<span style='font-size:0.7em;color:#b8c0d0;'>{st.session_state.user} ({role}) 님</span>"
        f"</div>",
        unsafe_allow_html=True)
with top_r:
    if st.button("로그아웃", use_container_width=True):
        st.session_state.user = None
        st.session_state.selected_date = None
        st.query_params.clear()
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
        st.session_state.selected_date = None
        st.rerun()
with nav_c:
    st.markdown(
        f"<h3 style='text-align:center;margin:0;color:#e6e6e6;'>"
        f"{st.session_state.view_year}년 {st.session_state.view_month}월</h3>",
        unsafe_allow_html=True)
with nav_r:
    if st.button("다음 달 ▶", use_container_width=True):
        st.session_state.view_month += 1
        if st.session_state.view_month > 12:
            st.session_state.view_month = 1
            st.session_state.view_year += 1
        st.session_state.selected_date = None
        st.rerun()

st.write("")

# ──────────────────────────────────────────────
# 달력 렌더링 (칸 자체가 클릭 버튼)
# ──────────────────────────────────────────────
year = st.session_state.view_year
month = st.session_state.view_month
month_tasks = get_tasks_for_month(year, month)

weekday_names = ["월", "화", "수", "목", "금", "토", "일"]

cal = calendar.Calendar(firstweekday=0)  # 월요일 시작
weeks = cal.monthdayscalendar(year, month)
today = date.today()


def esc(s):
    return (s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;"))


# 요일 헤더
head_html = "<div class='cal-grid'>"
for i, wn in enumerate(weekday_names):
    color = "#ef5350" if i == 6 else ("#42a5f5" if i == 5 else "#cfcfcf")
    head_html += f"<div class='cal-head' style='color:{color};'>{wn}</div>"
head_html += "</div>"

# 날짜 본문
body_html = "<div class='cal-grid'>"
for week in weeks:
    for i, day in enumerate(week):
        if day == 0:
            body_html += "<div class='cal-cell empty'></div>"
            continue

        wd_str = f"{year:04d}-{month:02d}-{day:02d}"
        tasks = month_tasks.get(wd_str, [])
        is_today = (today.year == year and today.month == month and today.day == day)

        day_color = "#ef5350" if i == 6 else ("#42a5f5" if i == 5 else "#e6e6e6")
        cell_cls = "cal-cell today" if is_today else "cal-cell"

        inner = f"<div class='cal-daynum' style='color:{day_color};'>{day}</div>"
        for leader, task, num, workers in tasks:
            c = count_color(num)
            w_txt = f"({esc(workers)})" if workers else ""
            inner += (
                f"<div class='cal-task'>"
                f"<span class='lead'>{esc(leader)}</span><br>"
                f"<span class='desc'>{esc(task)}</span><br>"
                f"<span style='color:{c};font-weight:700;'>{num}명{w_txt}</span>"
                f"</div>"
            )

        # 칸 전체를 링크로 → 클릭 시 ?u=이름&d=날짜 로 이동 (로그인 유지)
        body_html += (
            f"<a class='{cell_cls}' "
            f"href='?u={st.session_state.user}&d={wd_str}' target='_self'>{inner}</a>"
        )
body_html += "</div>"

st.markdown(head_html, unsafe_allow_html=True)
st.markdown(body_html, unsafe_allow_html=True)

st.divider()

# ──────────────────────────────────────────────
# 선택된 날짜 상세 (작업 입력 / 메모)
# ──────────────────────────────────────────────
if st.session_state.selected_date:
    sel = st.session_state.selected_date
    st.markdown(f"<h2 style='color:#e6e6e6;'>🗓️ {sel} 상세</h2>", unsafe_allow_html=True)

    left, right = st.columns(2)

    # ── 작업 일정 ──
    with left:
        st.markdown("<h3 style='color:#e6e6e6;'>📋 작업 일정</h3>", unsafe_allow_html=True)
        existing = get_tasks_by_date(sel)
        if existing:
            for tid, leader, task, num, workers in existing:
                c = count_color(num)
                w_txt = f"({workers})" if workers else ""
                box, btn = st.columns([5, 1])
                box.markdown(
                    f"<div style='background:#1a1f2b;border-left:5px solid {c};"
                    f"border-radius:8px;padding:10px 14px;margin:4px 0;'>"
                    f"<div style='font-size:16px;font-weight:700;color:#ffffff;'>{leader}</div>"
                    f"<div style='font-size:15px;margin:2px 0;color:#d6d6d6;'>{task}</div>"
                    f"<div style='font-size:15px;color:{c};font-weight:700;'>{num}명{w_txt}</div>"
                    f"</div>",
                    unsafe_allow_html=True)
                if btn.button("🗑", key=f"deltask_{tid}"):
                    delete_task(tid)
                    st.rerun()
        else:
            st.info("등록된 작업이 없습니다.")

        st.markdown("<h4 style='color:#e6e6e6;'>➕ 작업 추가</h4>", unsafe_allow_html=True)

        # 팀장이면 이름 고정, 팀원이면 선택
        if st.session_state.user in TEAM_LEADERS:
            leader_sel = st.session_state.user
            st.text_input("팀장", value=leader_sel, disabled=True, key="leader_fixed")
        else:
            leader_sel = st.selectbox("팀장 선택", TEAM_LEADERS, key="leader_sel")

        task_input = st.text_input("작업 내용", placeholder="예) 국민연금 추가작업", key="task_input")
        num_sel = st.number_input("필요 팀원 수", min_value=1, max_value=4, value=1, step=1, key="num_sel")
        worker_sel = st.multiselect("투입 팀원 (선택)", WORKERS, key="worker_sel")

        if st.button("작업 등록", type="primary", use_container_width=True):
            if task_input.strip():
                add_task(sel, leader_sel, task_input.strip(), int(num_sel), worker_sel)
                st.success("등록되었습니다.")
                st.rerun()
            else:
                st.warning("작업 내용을 입력하세요.")

    # ── 메모 (팀간 소통) ──
    with right:
        st.markdown("<h3 style='color:#e6e6e6;'>💬 메모 (팀간 소통)</h3>", unsafe_allow_html=True)
        memos = get_memos_by_date(sel)
        if memos:
            for mid, author, content, created in memos:
                box, btn = st.columns([6, 1])
                box.markdown(
                    f"<div style='background:#2a2410;border-radius:8px;"
                    f"padding:8px 14px;margin:4px 0;'>"
                    f"<b style='color:#ffd54f;'>{author}</b> "
                    f"<span style='color:#9a9a9a;font-size:11px;'>{created}</span><br>"
                    f"<span style='color:#e6e6e6;'>{content}</span></div>",
                    unsafe_allow_html=True)
                if btn.button("🗑", key=f"delmemo_{mid}"):
                    delete_memo(mid)
                    st.rerun()
        else:
            st.info("메모가 없습니다.")

        st.markdown("<h4 style='color:#e6e6e6;'>✏️ 메모 작성</h4>", unsafe_allow_html=True)
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
    st.info("달력에서 날짜 칸을 클릭하면 작업 입력과 메모를 작성할 수 있습니다.")
