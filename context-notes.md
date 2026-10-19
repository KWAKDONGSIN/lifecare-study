# 결정과 이유

- 2026-10-19 · 요청: 기존 사이트(Cloudflare workers.dev, 한 파일 앱)가 폰에서 "작동을 안 함" → 처음부터 다시 설계한 새 사이트. GitHub 공개 OK.
- 원인은 재현 못 함 — 최신 크롬(모바일 에뮬레이션)에선 정상, 콘솔 오류 없음. 카톡 인앱 브라우저·통신망(workers.dev)·한 파일 300KB 스크립트 중 하나로 추정. 그래서 새 설계는 이 셋을 모두 피한다.
  - **장마다 정적 HTML 한 페이지.** 글·그림은 JS 없이 다 보인다. 서술형·암기카드는 `<details>`라 JS 불필요.
  - **낱말 밑줄은 빌드 때 HTML 링크로 박는다** (`words.html#wN`). JS가 돌면 뜻 창, 안 돌면 낱말사전으로 이동.
  - JS(`assets/app.js`)는 구형 문법(var·function)만. 외부 글꼴·CDN 없음.
  - 배포는 GitHub Pages(`docs/` 폴더) — github.io는 국내에서 잘 열린다.
- 본문은 10/19에 15세 눈높이로 새로 쓴 `content/easy/c0~c9.html`을 그대로 쓴다. 예전 "더 깊이 보기" 원문 개념은 뺐다(쉬운 본문에 시험 사실이 다 들어가 있음).
- 공개 저장소라 교수님 슬라이드 27장도 공개된다 — 사용자가 "공개돼도 상관없다"고 함.
- 다시 만들기: `python build.py` → `docs/` 커밋·푸시하면 Pages가 갱신된다.
- 배포 2026-10-19 — https://kwakdongsin.github.io/lifecare-study/ (공개 저장소 KWAKDONGSIN/lifecare-study, Pages=main/docs). 실제 주소에서 폰 너비·낱말 창·이미지 확인, 카카오톡(나에게)으로 주소 전송.
