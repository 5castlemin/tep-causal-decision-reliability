# 복구 절차

태그가 원격에서 검증됐는지 먼저 확인한다: `git ls-remote --tags origin "attic/2026-11-10/*"`. 각 annotated tag의 `^{}`가 매니페스트의 원래 commit SHA와 같아야 한다. `git fetch origin --tags` 후 `git rev-parse "attic/2026-11-10/feature/<원래이름>^{commit}"`으로 다시 확인하고, `git switch -c restore/<이름> "attic/2026-11-10/feature/<원래이름>^{commit}"`로 새 브랜치에서 복구한다. 태그나 원래 기록을 force 변경하지 않는다.

태그는 Git이 추적한 객체만 보존한다. `data/local/`이나 원시자료·대용량 외부 파일은 별도의 권한·원본·해시 검증 및 보관 경로가 필요하며 이 문서만으로 재배포나 팀 접근이 보장되지 않는다. PR 이력과 토론은 GitHub PR 링크를 통해 확인한다.
