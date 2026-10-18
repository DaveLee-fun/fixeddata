# Jev 1.14 vs GPT-6 Luna (OpenAI Decisions API) · 50문제

잔재미코딩 영상 "200배 빨라 난리났던 AI Jev, 벌써 더 좋아졌다!"에서 쓴 테스트 문제입니다 (2026-10-16 실행).

- `questions.json`: 50문제 (영어 이미지·한국어 이미지·영어 글·한국어 글·fun-coding.org SEO 각 10개). `truth`가 정답
- `images/`: 문제에 쓴 이미지 (메뉴판·오류 창·영수증·작은 글씨 쿠폰은 직접 만든 이미지)
- `run_compare.py`: 두 모델에 같은 이미지·같은 질문을 보내는 코드 (Jev: POST /v1/systemone + `TypeSafe-Danger-Zone-Images: true`, OpenAI: POST /v1/decisions, gpt-6-luna)

결과: Jev 1.14 48/50 (중앙값 0.27초), GPT-6 Luna 49/50 (0.37초). 둘 다 틀린 문제 ko_text_02, Jev만 틀린 문제 en_text_07.
- `results.json`: 문제별 두 모델의 답·확률·시간·입력 토큰 (영상에 쓴 실제 실행 결과)
