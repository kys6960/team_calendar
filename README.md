# 📅 팀 공유 일정 달력 (team_calendar.py)

여러 팀이 날짜별 작업·필요 인력을 공유하고, 메모로 서로 소통하는 Streamlit 웹앱입니다.

## 구성원 정의 (코드 상단에서 수정 가능)
- 팀장 : 서유석, 홍영태, 김수용
- 인력 : 김만두, 박순일, 고한명, 서범석

## 주요 기능
1. **간단 로그인** — 본인 이름 버튼 클릭으로 입장 (비밀번호 없음)
2. **달력 UI** — 월 단위로 보기, 이전/다음 달 이동
3. **작업 등록** — 날짜를 열고 팀장 / 작업내용 / 필요인력 수 / 투입인력 입력
   - 화면 표시 형식 (한 화면에 모두 보임):
     ```
     서유석
     국민연금 추가작업
     2명(김만두,박순일)
     ```
   - 인력 수에 따라 색상 구분(1명 초록 / 2명 주황 / 3명+ 빨강)
4. **메모** — 다른 팀에게 남기는 날짜별 소통 메모 (작성자 이름 자동 기록)
5. **데이터 저장** — `team_calendar.db` (SQLite) 파일에 자동 저장 → 모두 같은 내용 공유

---

## 1. 로컬 실행
```bash
pip install streamlit
streamlit run team_calendar.py
```
실행 후 브라우저에서 `http://localhost:8501` 접속.

같은 사무실(같은 네트워크)에서 공유하려면:
```bash
streamlit run team_calendar.py --server.address 0.0.0.0
```
→ 다른 사람은 `http://<내PC_IP>:8501` 로 접속.

---

## 2. 외부 URL로 공유 (추천: Streamlit Community Cloud · 무료)
1. GitHub에 `team_calendar.py` 와 `requirements.txt` 업로드
2. https://share.streamlit.io 접속 → GitHub 연결 → 저장소 선택 → Deploy
3. 생성된 URL을 팀원들에게 전달

`requirements.txt` 내용:
```
streamlit
```

> ⚠️ 주의: Streamlit Cloud는 재배포 시 SQLite 파일이 초기화될 수 있습니다.
> 장기 보관이 중요하면 Google Sheets 연동이나 외부 DB(Supabase 등)로
> 바꾸는 것을 권장합니다. 필요하면 그 버전도 만들어 드릴게요.

---

## 구성원 변경 방법
코드 상단의 아래 부분만 수정하면 됩니다.
```python
TEAM_LEADERS = ["서유석", "홍영태", "김수용"]
WORKERS = ["김만두", "박순일", "고한명", "서범석"]
```
