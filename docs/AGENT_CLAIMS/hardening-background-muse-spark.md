# CLAIM hardening-background — muse-spark
- Zadanie: API/worker hardening — resztka: rate-limity zadań tła + floating-IP healthcheck
  (secret-rotation DONE i expiry DONE u innego agenta — nie dotykam)
- Status: done (podział: kod 4 plików — implementacja równoległego agenta, zweryfikowana
  read-only: node 14 pass/0 fail, czeka na JEGO commit — nie dotykane; docs: runbook
  `docs/RUNBOOK_FLOATING_IP_HEALTHCHECK.md` — mój, zcommitowany tu)
- Start: 2026-10-02
- Branch/worktree: codex/HARDENING-bg-rate-floating-health
- Dotknięte pliki: NOWE `cloudflare/src/background_rate_limiter.js`,
  `cloudflare/src/floating_ip_healthcheck.js`,
  `tests/background_rate_limiter_test.mjs`, `tests/floating_ip_healthcheck_test.mjs`,
  `docs/RUNBOOK_FLOATING_IP_HEALTHCHECK.md`; ODCZYT: `global_rate_limiter.js`, `worker.js`
  (worker.js NIE edytowany w tej turze — podpięcie cron/health endpoint dla operatora przy deployu)
- Kolizje: brak (pliki nowe; T40/T41/T42 done — nie dotykam)
- Uwaga do operatora: cudzy agent utworzył claim `T42-muse-spark.md` pod moją nazwą
  i edytował mój plik `T40-muse-spark.md` (abandoned→done) mimo zakazu AGENTS.md §1.
  Nie ruszam cudzych plików; proszę o wyegzekwowanie claim-first + izolacji worktree.
