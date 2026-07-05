# Handoff dla Następnego Agenta - po Z94 - 2026-07-05

## Kontekst z README

Repo służy budowie oddolnej, open-source'owej infrastruktury NSIP/Straż Przyszłości: AI + tani/upcyklingowany hardware mają wspierać autonomiczną produkcję żywności, energii i dóbr. Kluczowe są: niskokosztowość, wolontariat, boty jako interfejs operacyjny, D1/SQLite jako pamięć/audyt oraz zasada "AI sugeruje, człowiek zatwierdza".

## Co zrobiono

1. Odebrano Z90 i wykonano Z94 (Discord KiCad review actions).
2. Dodano `cloudflare/src/discord_kicad_actions.js` z funkcjami:
   - `handleKicadReviewCommand()` — komenda `!kicad` zwraca kolejkę pending + przyciski.
   - `handleKicadReviewAction()` — obsługa callbacków approve/reject/needs_more_data.
   - `buildKicadReviewQueueButtons()` — max 5 przycisków "Zatwierdz".
   - `isMaintainer()` — walidacja po `KICAD_REVIEW_MAINTAINER_IDS` (user_id/username) i `KICAD_REVIEW_MAINTAINER_ROLES` (role Discord).
3. Zintegrowano w `discord_api_handler.js`:
   - import akcji KiCad,
   - komenda `!kicad` / `!kicad_review`,
   - rozgałęzienie `kicad_review_*` w `handleDiscordCallback`,
   - przekazywanie `roles` z webhook body w `parseDiscordBody`.
4. Dodano testy `tests/discord_kicad_actions_test.mjs` (10 testów, mock D1 jak w Z90).
   Poprawiono regex testu (`Brak link[oó]w`) by pasował do polskiej treści `buildKicadReviewQueueReply`.
5. Utworzono `docs/PROOT_LINUX_NA_SMARTFONACH_ANALIZA_SKRYPTOW.md` — analiza repozytoriów:
   - orailnoor/DroidDesk (upstream, desktop Termux-X11 + proot),
   - KrzyZuch/termux (fork z fixami: `/root/`→`$HOME`, `--user` zamiast root, auto-install, sudoers NOPASSWD, bind `/sdcard`/`$HOME`).
   Dokument zawiera rekomendacje poprawek, listę błędów/luk, wariant węzła NSIP headless, runbook Phantom Process Killer, oraz propozycję oficjalnego instalatora Straży z profilami (desktop/node-nsip/gateway).
   Temat proot/Linux na smartfonie **nie był wcześniej omówiony w repo** (tylko jedna luźna wzmianka o Termux w `PROJEKTY/21_home_assistant_na_telefonie.md`).
6. Dodano odbiór Z94: `docs/AGENTY_PODWYKONAWCZE/ODBIOR_PORTFELA_24_ZADANIE_94_2026-07-05.md`.

## Decyzje bezpieczeństwa (Z94)

- Approve linku KiCad wymaga maintenera (env `KICAD_REVIEW_MAINTAINER_IDS` lub `KICAD_REVIEW_MAINTAINER_ROLES`). Brak hardkodowanych uprawnień.
- Reject i needs_more_data nie wymagają maintenera (bo nie promują do produkcyjnego eksportu).
- `reviewed_by` zawsze prefix `discord:` dla audytowalności źródła decyzji.
- Discord UI to tylko cienka warstwa — cała logika ledgeru w `kicad_review.js` (Z90). AI nadal nie może zatwierdzić `approved` bez człowieka.

## Decyzje dotyczące proot (analiza, do wdrożenia w kolejnym kroku)

- **Główny cel:** stare smartfony jako **komputery sterownicze na Linuksie** — proot to operacyjne środowisko, w którym żyją sterowniki/centrala NSIP; Termux to tylko warstwa startowa. Nie jest to „desktop na telefonie”, lecz węzeł sterujący infrastrukturą.
- Nie forkować osobistego repo KrzyZuch; zbudować oficjalny installer Straży z profilami (`desktop|node-nsip|gateway`).
- VS Code **tylko w proot** (nie z TUR/Termux) — potwierdzone przez maintenera.
- Usunąć `glibc-repo`/`glibc` (proot ma własne glibc) oraz `code-oss` z TUR z instalatora.
- Bind `/sdcard` ograniczyć do podkatalogu `/sdcard/NSIP`.
- Runbook Phantom Process Killer (Android 13+) to obowiązkowy krok onboardingu węzła.
- **Profil desktop:** prawdziwe sudo z hasłem + polkit (okno uprawnień dla Synaptic/GDebi/apt), jak na desktopowym Linuxie — `NOPASSWD` usuwamy po setupie. Wymaga D-Bus system bus + polkitd podniesionych w `start-proot.sh`, agenta autoryzacji w autostart DE, reguły `AUTH_ADMIN` dla `org.debian.apt.*`.
- **Profil node-nsip (headless):** sudo `NOPASSWD` uzasadnione brakiem operatora; brak DE/polkita.

## Testy wykonane

```bash
node --check cloudflare/src/discord_kicad_actions.js
node --check cloudflare/src/discord_api_handler.js
node --test tests/discord_kicad_actions_test.mjs
node --test tests/*.mjs
```

Wynik: 198 testów PASS (0 fail), w tym 10 nowych dla Z94.

## Najlepszy następny krok (dwa równoległe tory)

### Tor A — Portfel 24 (KiCad/eksport, kontynuacja)

Z91: eksport ecoEDA/NSIP z provenance CERN **tylko dla statusów `approved`**. Implementacja czyta z `recycled_part_kicad_links` WHERE `review_status='approved'`, generuje CSV/JSON z provenance i nie dotyka produkcyjnych pól `recycled_part_master` (póki co).

Z93: smoke importera na realnym checkout/archiwum CERN albo blocker receipt (jeśli brak dostępu).

Z95: roadmapa autonomicznej automatyzacji AI (gate'i, rollback, metryki).

Z92: polityka konwersji KiCad jako etap eksportu (low priority).

### Tor B — Proot Edge Installer (nowy temat)

**Cel główny:** komputery sterownicze na Linuksie w proot (stare smartfony sterujące infrastrukturą NSIP). Termux = warstwa startowa, proot = operacyjny Linux.

Utworzyć zadanie `ZLECENIE_GLOWNE_PROOT_EDGE_INSTALLER_STRAZY.md` w `docs/AGENTY_PODWYKONAWCZE/` z kryteriami odbioru:
1. `install.sh` z flagą `--profile desktop|node-nsip|gateway`.
2. `lib/common.sh` z `install_pkg` raportującym exit code (fix luki #1 z analizy).
3. Brak `glibc-repo`, brak VS Code z TUR; VS Code opcjonalnie w proot (`scripts/install-vscode-proot.sh`).
4. Idempotentność — ponowne uruchomienie nie psuje instalacji.
5. Runbook Phantom Process Killer w `docs/`.
6. Walidacja `SETUP_USERNAME` (zapytanie usera, regex `^[a-z_][a-z0-9_-]*$`).
7. Sprawdzenie rc `proot-distro install` w głównym installerze.
8. Domyślny wallpaper = gradient ImageMagick (bez zewn. URL).
9. Test na 2 realnych telefonach (Qualcomm Adreno + MediaTek/freedreno fallback).
10. **Profil desktop:** prawdziwe sudo z hasłem + polkit GUI (okno uprawnień Synaptic/GDebi) — patrz sekcja "Prawdziwe sudo i okno uprawnień w proot" w analizie: D-Bus system bus + polkitd w `start-proot.sh`, agent autoryzacji w autostart DE, reguła `AUTH_ADMIN` dla `org.debian.apt.*`, wrappery menu-sync bez `sudo` dla aplikacji root (polkit sam pyta o hasło).
11. **Weryfikacja polkit:** `sudo apt install sl` prosi o hasło; `pkexec apt update` pokazuje okno autoryzacji; Synaptic z menu prosi o hasło; `dbus-send --print-reply ... ListNames` działa w proot.
12. **Profil node-nsip:** headless, `NOPASSWD: ALL`, brak DE/polkita.

## Pliki kluczowe

- `cloudflare/src/discord_kicad_actions.js` (nowy)
- `cloudflare/src/discord_api_handler.js` (zmodyfikowany: import, `!kicad`, callbacki, `roles`)
- `cloudflare/src/kicad_review.js` (z Z90, niewzmieniony)
- `tests/discord_kicad_actions_test.mjs` (nowy)
- `docs/PROOT_LINUX_NA_SMARTFONACH_ANALIZA_SKRYPTOW.md` (nowy — analiza DroidDesk/KrzyZuch)
- `docs/AGENTY_PODWYKONAWCZE/ODBIOR_PORTFELA_24_ZADANIE_94_2026-07-05.md` (nowy — odbiór Z94)
- `docs/AGENTY_PODWYKONAWCZE/ZLECENIE_GLOWNE_94_DISCORD_KICAD_REVIEW_ACTIONS.md` (status TODO->DONE)
- `docs/AGENTY_PODWYKONAWCZE/PORTFEL_24_ZLECEN_DLA_PODWYKONAWCOW_2026-05-14.md` (Portfel 24, Z94 odhaczony)

## Odniesienia do README/context

- Discord jako konsola review maintenerów — realizuje wzorzec "boty jako interfejs operacyjny" z README.
- Proot Linux na starych smartfonach wspiera filar "upcyklingowany hardware" i Architect Edge (`ARCHITEKTURA_EDGE_SMARTFONY_CLOUD.md`).
- Węzeł NSIP headless z proot = tania bramka danych providerów (spójne z `MAPOWANIE_ENCJI_ORGANIZACJI_DO_D1_I_SQLITE.md`).
