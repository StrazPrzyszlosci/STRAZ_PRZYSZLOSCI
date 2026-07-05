# Proot Linux na Starych Smartfonach - Analiza Skryptów Instalacyjnych i Rekomendacje dla Straży Przyszłości

## Kontekst

Z **starych smartfonów robimy komputery sterownicze bazujące na Linuksie**. Smartfon staje się operacyjnym środowiskiem sterowania infrastrukturą NSIP (pompami, oświetleniem, czujnikami, aktuatorami, agentami). Termux to tylko warstwa startowa; **proot to właściwy, pełnoprawny Linux** (więcej możliwości niż czysty Termux), w której żyją sterowniki/centrala i narzędzia operacyjne — bez rootowania Androida.

W proot ma działać **jak w prawdziwym Linuxie**:
- w terminalu `sudo apt install …` (z prośbą o hasło lub bez — konfigurowalne),
- z menu/pulpitu aplikacje wymagające root (np. Synaptic, GDebi) uruchamiane z **oknem uprawnień** (polkit GUI), jak na desktopowej dystrybucji.

Powiązane dokumenty:
- [ARCHITEKTURA_EDGE_SMARTFONY_CLOUD.md](ARCHITEKTURA_EDGE_SMARTFONY_CLOUD.md)
- [../PROJEKTY/06_smartfony_jako_sterowniki.md](../PROJEKTY/06_smartfony_jako_sterowniki.md)
- [../PROJEKTY/21_home_assistant_na_telefonie.md](../PROJEKTY/21_home_assistant_na_telefonie.md)

Powiązane dokumenty:
- [ARCHITEKTURA_EDGE_SMARTFONY_CLOUD.md](ARCHITEKTURA_EDGE_SMARTFONY_CLOUD.md)
- [../PROJEKTY/06_smartfony_jako_sterowniki.md](../PROJEKTY/06_smartfony_jako_sterowniki.md)
- [../PROJEKTY/21_home_assistant_na_telefonie.md](../PROJEKTY/21_home_assistant_na_telefonie.md)

## Źródła

- **Główne (upstream):** https://github.com/orailnoor/DroidDesk — pełny desktop Termux-X11 + proot Ubuntu/Debian/Kali, GPU Turnip/Zink, mostek menu proot→XFCE.
- **Fork (KrzyZuch):** https://github.com/KrzyZuch/termux — customizacja pod potrzeby osobiste, nie pod ogólne użycie Straży. Wprowadza wartościowe fixy, ale też zbędne/osobiste elementy.

## Czy temat był już omówiony w repo

Nie. W repo Termux pojawia się tylko raz — w `PROJEKTY/21_home_assistant_na_telefonie.md` jako link do instalatora HA Core. Brak dokumentu o proot jako operacyjnym Linuksie na smartfonie, brak analizy DroidDesk/KrzyZuch, brak rekomendacji skryptów. Niniejszy dokument wypełnia tę lukę.

## Co naprawiono w forku KrzyZuch (wartościowe, do zachowania)

| Zmiana | Dlaczego dobra |
|--------|----------------|
| `SETUP_USERNAME="user"` zamiast `"root"` | proot startuje jako zwykły użytkownik z sudo; to bezpieczniejsze i zgodne z celem (nie czysty root) |
| `/root/` → `$HOME`/`${HOME}` w skryptach i plikach `.desktop` | Termux HOME to `/data/data/com.termux/files/home`, nie `/root` — fix ścieżek zapobiega niedziałającym autostartom |
| Auto-instalacja proot distro w `start-proot.sh` gdy brakuje | user nie musi pamiętać o `proot-distro install` |
| `--user $SETUP_USERNAME` zamiast `--user root` w `proot-distro login` | sesja proot jako user, nie root — zgodne z celem |
| Bind `/sdcard` i `$HOME` (`/termux-home`) do proot | współdzielenie plików między Termux/proot a pamięcią telefonu |
| `"${2:-user}"` — `PROOT_USER` jako 2. argument `proot-menu-sync.sh` | wrappery aplikacji uruchamiane jako user, nie root |
| Sygnalizacja Phantom Process Killer + komenda `adb` | Android 13+ zabija proot (signal 9); instrukcja to niezbędny runbook |
| `/etc/sudoers.d/proot-compat` z `NOPASSWD` i `!requiretty` | sudo działające bez hasła i bez TTY w proot |

## Co usunąć/zmienić względem forku (nie pasuje do Straży)

| Element w forku | Rekomendacja | Uzasadnienie |
|------------------|--------------|-------------|
| `install_pkg "glibc-repo"` + `glibc` | **USUNĄĆ** | glibc-repo/TUR to zaawansowana, niestandardowa warstwa kompatybilności; dla węzłów Straży generuje problemy zależności i konfliktów. Standardowy proot Debian/Ubuntu ma natywne glibc — nie trzeba dokładać drugiego glibc w Termux |
| `vulkan-loader` + `vulkan-tools` zamiast `vulkan-loader-android` | **SPRAWDŹ warunkowo** | `vulkan-loader-android` to właściwy(loader pod Mesa Turnip na Androidzie). KrzyZuch zamienił, by działało z glibc-repo. Bez glibc-repo zostaw `vulkan-loader-android` (upstream). `vulkan-tools` opcjonalnie dla diagnostyki |
| `code-oss` z TUR + skrót `~/Desktop` | **USUNĄĆ z Installera** | VS Code w Termux/TUR działa gorzej niż w proot. **VS Code powinien być instalowany TYLKO w proot** (przez `apt` lub dedykowany wrapper proot), gdzie ma natywne glibc i sandbox. Patrz sekcja "VS Code w proot" |
| Skróty desktop dla `PhoneStorage`/`TermuxHome` | **WYDZIELIĆ jako opcjonalne** | wygodne dla desktopu użytkownika, ale nie eseń wezła; zostawić jako flagę |
| Synaptic/GDebi (`sudo synaptic`/`sudo gdebi-gtk`) | **ZACHOWAĆ + dodać polkit GUI** | węzeł-as-komputer sterowniczy korzysta z graficznych narzędzi root (Synaptic) jak desktopowy Linux — uruchomione z menu mają pokazywać okno uprawnień, a nie `sudo NOPASSWD` w wrapperze. Patrz sekcja "Prawdziwe sudo i okno uprawnień w proot" |

## VS Code w proot (wymagane podejście)

VS Code (code) instalowany **wyłącznie w proot**, nie w Termux:

```bash
bash ~/start-proot.sh
# wewnątrz proot jako user:
sudo apt update
sudo apt install -y code gnupg curl
# albo (bez repo MS, lżejszy):
# sudo apt install -y code-oss
exit
bash ~/proot-menu-sync.sh
```

`proot-menu-sync.sh` z forku (z gałęzią `code`) już ma poprawkę `--no-sandbox` i `--user-data-dir=/root/.vscode-root` — tę logikę **zachować**, bo VS Code w proot wymaga `--no-sandbox` (sandbox nie działa pod proot z niedziałającym userns).

Rekomendacja: dodać do installer opcjonalny krok "VS Code w proot", który instancjuje proot i uruchamia `apt install code`, a wrapper menu-sync obsługuje resztę.

## Błędy i luki znalezione w obu skryptach (upstream + fork)

### Krytyczne

1. **Brak idempotentności kroków apt.** `install_pkg` tłumi błędy (`> /dev/null 2>&1`) i `spinner` raportuje sukces nawet przy porażce — user nie wie, że np. `xfce4` się nie zainstalował. **Fix:** przechwyć exit code i wypisz ostrzeżenie:
   ```bash
   install_pkg() {
       local pkg=$1 name=${2:-$pkg}
       (DEBIAN_FRONTEND=noninteractive apt-get install -y \
           -o Dpkg::Options::="--force-confold" "$pkg" > /tmp/pkg-$$.log 2>&1) &
       local pid=$!
       spinner $! "Installing ${name}..."
       local rc=$?
       [ $rc -ne 0 ] && { echo -e "  ${RED}[!] $pkg FAILED (rc=$rc). Log: /tmp/pkg-$$.log${NC}"; }
       return $rc
   }
   ```

2. **`SETUP_USERNAME` brak walidacji.** upstream ma hardkoded `root`, fork `user`. Brak pytania. User o nazwie `user` może kolidować. **Fix:** zapytaj i zweryfikuj (`^[a-z_][a-z0-9_-]*$`).

3. **`xfce-first-run.desktop` używa `bash /root/.config/...`** (upstream) — fork poprawił na `${HOME}`, ale heredoc zmieniono z `'AREOF'` na `AREOF` (rozwijanie zmiennych) — jeśli w bloku są znaki specjalne, mogą się rozwinąć. Tu akurat bezpieczne, ale **rekomenduj zostawić `'AREOF'` (quoted) i hardkodować ścieżkę przez `sed`**, albo użyć `$HOME` bez cudzysłowu heredoc — tak jak fork, ale udokumentować.

4. **Brak weryfikacji instalacji proot przed `proot-distro login`.** upstream zakłada, że install się udał. Fork dodał auto-install w `start-proot.sh`, ale **główny installer (`step_proot`) wciąż nie sprawdza rc `proot-distro install`** — idzie dalej nawet przy porażce pobierania. **Fix:**
   ```bash
   if ! proot-distro install "$PROOT_DISTRO"; then
       echo -e "${RED}[!] Nie udało się zainstalować $PROOT_LABEL. Sprawdź sieć/pamięć.${NC}"
       return 1
   fi
   ```

5. **`--user root` w `proot-menu-sync.sh` wrappery** (upstream) — fork poprawił na `--user "$PROOT_USER"`, ale domyślnie `$2` to `user`. Jeśli user proot nazywa się inaczej, aplikacje launchowane jako nieistniejący user zawiodą. **Fix:** przekazuj username konsekwentnie z `step_proot` przez zmienną środowiskową i sprawdzaj istnienie usera w proot.

### Bezpieczeństwo

6. **`/etc/sudoers.d/proot-compat: NOPASSWD: ALL`** — obecnie sudo bez hasła dla wszystkiego. To wygodne do jednorazowego setupu, ale **nie zachowuje się jak prawdziwy Linux**: nie prosi o hasło, nie pokazuje okna uprawnień dla aplikacji graficznych root (Synaptic). **Fix:** po setupie zamienić na sudo z hasłem + polkit (patrz sekcja "Prawdziwe sudo i okno uprawnień w proot"). NOPASSWD zostawić tylko dla wariantu headless/bezobsługowego.

7. **`termux-x11 :0 -ac`** — flaga `-ac` wyłącza auth na X serwerze. Każdy proces lokalny może podłączyć się do ekranu. Na smartfonie jednoużytkownikowym akceptowalne, ale **udokumentować i dla węzła wieloosobowego usunąć `-ac`** i dodać `xauth`.

8. **Bind `/sdcard` do proot (fork)** — odsłania całą pamięć telefonu wewn. proot. Dla bramki danych OK, ale **dla proot z nieufnymi narzędziami** (np. Metasploit) ryzykowne. **Fix:** opcjonalny bind tylko do dedykowanego podkatalogu: `--bind /sdcard/NSIP:/nsip-data`.

9. **Wallpaper pobierany przez `wget` z `wallpapercave.com`** — zewnętrzny URL, potencjalny tracking i nieprzewidywalny content. **Fix:** usuń URL z domyślnej konfiguracji; zostaw gradient ImageMagick jako domyślny. Straż nie potrzebuje Ubuntu wallpaper.

### Robustność / UX

10. **`TOTAL_STEPS=12`, ale `step_vnc_optional` poza licznikiem** — progress nie obejmuje VNC. Drobne, ale mylące.

11. **Komentarz `# SETUP_USERNAME_PROMPT\nexport PS1=...`** w `main()` — `\n` to literalny backslash-n w echo, nie newline. **Fix:** użyj `printf` lub dwóch `echo`.

12. **`source "$BASHRC" 2>/dev/null`** w skrypcie nieinteraktywnym może nie zadziałać i nie jest potrzebne (skrypt się kończy). Usunąć.

13. **`Kali Linux` przez `kali-nethunter`** — `proot-distro` używa nazwy `kali` (nie `kali-nethunter`) w nowszych wersjach. **Sprawdź** `proot-distro list` na urządzeniu — może wymagać `PROOT_DISTRO="kali"`.

14. **Brak sprawdzania dysku/baterii** przed długim install. Dodaj ostrzeżenie: "Podłącz ładowarkę, install potrwa do X min".

15. **Brak wariantu headless.** Cały installer skupia się na desktop X11. Dla węzła NSIP bez ekranu potrzebny jest **tryb minimalny: tylko proot + agenty + bufor**, bez DE. Patrz sekcja "Wariant węzła NSIP".

## Prawdziwe sudo i okno uprawnień w proot (kluczowe wymaganie)

W proot chcemy, by zachowanie było identyczne z desktopowym Linuxem:
- w terminalu: `sudo apt install <pkg>` prosi o hasło usera,
- z menu/pulpitu Synaptic/GDebi uruchamia się **bez** wpisywania `sudo` w wrapperze — system sam pokazuje **okno uprawnień** (polkit GUI) z prośbą o hasło administratora.

### Dlaczego domyślny proot tego nie ma

proot `login` startuje środowisko bez inita/systemd, więc:
- brak D-Bus **system bus** (session bus bywa, ale to za mało),
- brak działającego `polkitd` jako usługa,
- brak agenta autoryzacji polkit (`polkit-gnome-authentication-agent`),
- `gksu`/`pkexec` nie działa, bo nie ma PolicyKit do potwierdzenia.

Ponadto uprawnienia `setuid`/`cap` w proot są emulowane — `sudo` działa tylko dzięki temu, że cała sesja proot już ma efektywne UID 0 (prootRuntime przekłada realnego usera na uid 0 wewnątrz). Dlatego `sudo` w proot „działa” nawet bez prawdziwego setuid.

### Checklist konfiguracji „prawdziwego Linuxa” w proot

Instalator `step_proot` ma wykonać następujące kroki (poza obecnym tworzeniem usera):

**1. Ustaw hasło usera** (zamiast bezhasłowego sudo):
```bash
proot-distro login "$PROOT_DISTRO" -- bash -c "
  echo '$SETUP_USERNAME:$PROOT_USER_PASSWORD' | chpasswd
  # root też hasło (do polkit admin)
  echo 'root:$PROOT_ROOT_PASSWORD' | chpasswd
"
```

**2. Zamień `NOPASSWD` na sudo z hasłem** — `/etc/sudoers.d/proot-compat`:
```
Defaults !requiretty
$SETUP_USERNAME ALL=(ALL) ALL
```
(viola `NOPASSWD` usunięte). `!requiretty` zostaje — proot nie ma TTY standardowo dla GUI.

**3. Zainstaluj stos polkit:**
```bash
proot-distro login "$PROOT_DISTRO" -- apt-get install -y \
  policykit-1 \
  polkitd \
  polkit-kde-agent-1   # lub polkit-gnome-authentication-agent-1 (zależnie od DE)
```
Dla XFCE4 preferuj `policykit-1-gnome` + `polkit-gnome-authentication-agent-1`. LXQt → `polkit-qt-1-1`. KDE → `polkit-kde-agent-1`.

**4. Uruchom D-Bus system bus i polkitd przy starcie proot.** Zmodyfikuj `start-proot.sh`, by przed oddaniem powłoki podniósł usługi:
```bash
proot-distro login "\$PROOT_DISTRO" \$BINDS --user root -- /bin/bash -c "
  mkdir -p /run/dbus
  dbus-daemon --system --fork 2>/dev/null || true
  /usr/lib/policykit-1/polkitd --no-debug 2>/dev/null &
  exec su -l '$SETUP_USERNAME' -c 'bash --rcfile \$_RC'
" 2>/dev/null
```
Notatka: proot `--user root` wewnętrznie, a potem `su -l user` z czystym login shellem. Bezpośrednie `--user user` z graficznymi narzędziami polkit często nie podnosi usług — dlatego tu najpierw root startuje demony, potem zrzuca do usera.

**5. Agent autoryzacji w sesji graficznej.** W `~/.config/autostart/` (XFCE) dodać:
```
[Desktop Entry]
Type=Application
Name=PolicyKit Authentication Agent
Exec=/usr/lib/policykit-1-gnome/polkit-gnome-authentication-agent-1
X-GNOME-Autostart-enabled=true
NoDisplay=true
```
(`Exec` zależy od DE — patrz pkt 3.)

**6. Reguły polkit dla Synaptic/GDebi/apt.** Domyślnie `org.debian.apt.*` w Debianie/Ubuntu pozwala adminom na funkcje apt bez hasła dla niektórych akcji, ale pełne `install`/`update` pyta. Dla spójności dodaj jawny `pkla` w `/etc/polkit-1/rules.d/49-nsip-no-password.rules`:
```javascript
polkit.addRule(function(action, subject) {
    if (action.id.indexOf("org.debian.apt.") === 0 &&
        subject.isInGroup("sudo")) {
        return polkit.Result.AUTH_ADMIN;
    }
    return polkit.Result.NOT_HANDLED;
});
```
`AUTH_ADMIN` wymusi okno z hasłem admina — dokładnie to, czego chcemy. (`YES` dałoby bez hasła, `NO` blokowałoby.)

**7. Naprawa menu-sync dla aplikacji root.** Obecnie fork wrzuca `APP_CMD="sudo synaptic"` (NOPASSWD). **Zmień na uruchomienie bez sudo w wrapperze, niech polkit poprosi**:
```bash
if echo "$appname" | grep -qi "synaptic|gdebi"; then
    APP_CMD="$CLEAN_EXEC"   # bez sudo — polkit sam zapyta o hasło
fi
```
To jest zgodne z desktopową konwencją: klikasz Synaptic w menu, wstaje okno autoryzacji, wpisujesz hasło, aplikacja startuje.

### Weryfikacja odbioru

- `sudo apt install sl` prosi o hasło usera (nie `NOPASSWD`).
- `synaptic` uruchomiony z menu proot przez mostek pokazuje okno autoryzacji polkit.
- `pkexec apt update` pyta o hasło admina (działający polkit agent w sesji graficznej).
- `dbus-send --system --print-reply --dest=org.freedesktop.DBus /org/freedesktop/DBus org.freedesktop.DBus.ListNames` zwraca listę usług wewnątrz proot — potwierdza system bus.

### Tryb bezobsługowy (headless)

Dla węzła bez operatora (profil `node-nsip`): brak GUI/polkita. Wtedy:
- sudo `NOPASSWD: ALL` uzasadnione (brak operatora),
- lub zasadziej ograniczyć do konkretnych binarek które używają agenty (`/usr/local/bin/nsip-*`).

## Rekomendowana struktura skryptu dla Straży Przyszłości

Nie forkować osobistego repo. Utworzyć **oficjalny installer Straży** z modularnymi profilami:

```
straz-edge/
  install.sh            # główny: wybór profilu
  profiles/
    desktop.sh          # pełny desktop X11 (na bazie DroidDesk, z fixami)
    node-nsip.sh        # minimal: proot + agenty + bufor, headless
    gateway.sh          # bramka danych: proot + bridge ESP32/sensorów
  lib/
    common.sh           # spinner, install_pkg z rc, walidacja, idempotentność
    proot.sh            # setup proot + user + sudoers + wrapper menu-sync
    gpu.sh              # detekcja Adreno/zink, warunkowe pakiety
  scripts/
    start-proot.sh      # gostowanie
    proot-menu-sync.sh  # sync aplikacji proot→menu
    stop-linux.sh
```

Profil domyślny dla większości wolontariuszy: `node-nsip` (lekki). `desktop` opcjonalny dla operatora z monitorem.

## Wariant węzła NSIP (headless, zalecany dla Straży)

Węzeł operacyjny nie potrzebuje XFCE. Minimalny profil:

- Termux + `proot-distro` + `proot`
- proot Debian/Ubuntu (nie Kali — to overhead security tools)
- W proot jako user z sudo:
  - `nodejs`, `python3`, `git`, `curl`, `sqlite3`
  - agenty Straży (np. klient Cloudflare API, bufor obserwacji)
  - `cron` / `systemd-user` do harmonogramów
  - opcjonalnie `tailscale` lub WireGuard do bezpiecznego dostępu
- Brak `x11-repo`, `tur-repo`, DE, GPU — oszczędność ~1.5 GB i baterii
- VS Code przez SSH/Code-Server (w proot) opcjonalnie

Uruchamianie prostych serwisów w proot przez `proot-distro login -- /usr/local/bin/node-agent.sh` z `nohup` lub `tmux`.

## Poprawki do bezpośredniego zastosowania w forku KrzyZuch (jeśli chcesz pushować PR)

1. Usuń `install_pkg "glibc-repo"` i `install_pkg "glibc"` — proot ma własne glibc.
2. Przywróć `vulkan-loader-android` (zostaw `vulkan-tools` jako opcjonalny).
3. Usuń `install_pkg "code-oss"` i skrót VS Code z instalatora — przenieś do osobnego pliku `scripts/install-vscode-proot.sh` (działanie w proot).
4. Dodaj sprawdzanie exit code w `install_pkg` (patrz fix #1).
5. Dodaj walidację `SETUP_USERNAME` (zapytaj usera).
6. Sprawdź rc `proot-distro install` w `step_proot`.
7. Usuń domyślny `WALLPAPER_URL` — zostaw gradient domyślnie.
8. Ogranicz bind `/sdcard` do `/sdcard/NSIP` (flaga `--full-sdcard`).
9. Przekonfiguruj `synaptic`/`gdebi` w `proot-menu-sync.sh`: **nie** uruchamiaj przez `sudo synaptic` (NOPASSWD), lecz przez polkit (`synaptic` bez sudo, okno uprawnień pyta o hasło). Patrz sekcja "Prawdziwe sudo i okno uprawnień w proot".
10. Napraw `# SETUP_USERNAME_PROMPT\n` → multiline `printf`.

## Runbook Phantom Process Killer (Android 13+)

Bez tego proot pada z `signal 9` po kilku minutach. Dla każdego telefonu węzła:

```bash
# raz, przez ADB z PC:
adb shell "/system/bin/device_config put activity_manager max_phantom_processes 2147483647"
adb shell "/system/bin/device_config put activity_manager max_phantom_processes 2147483647"  # potwierdzenie
# alternatywa (per-app, nie wymaga adb po każdym restarcie):
# Ustawienia → Opcje programisty → Wyłącz ograniczenia procesów w tle dla Termux
```

Dodać do runbooka onboardingu węzła stały krok weryfikacji: `adb shell device_config get activity_manager max_phantom_processes`.

## Status wdrożenia

- **Gotowe do zaadaptowania:** DroidDesk upstream jako baza desktop + fixy z forku KrzyZuch (ścieżki, `--user`, auto-install, sudoers).
- **Do zbudowania:** oficjalny installer Straży z profilami (desktop/node-nsip/gateway), modularna lib/common.sh.
- **Do ustandaryzowania:** envkonfiguracja węzła (`provider_id`, `NSIP_API_URL`, write token) wstrzykiwana do proot, nie hardkodowana w skrypcie.
- **Następny krok:** utworzyć zadanie dla agenta podwykonawcy: "ZLECENIE_GLOWNE_PROOT_EDGE_INSTALLER_STRAZY" z kryteriami: profile desktop/node-nsip, idempotentność, VS Code tylko w proot, runbook Phantom Killer, brak glibc-repo/VS Code TUR.

## Decyzje bezpieczeństwa

- **Desktop (`profile=desktop`):** sudo z hasłem + polkit (okno uprawnień) — jak na desktopowym Linuxie. NOPASSWD usuwamy po setupie. Operator widzi okno autoryzacji dla Synaptic/GDebi.
- **Headless (`profile=node-nsip`):** NOPASSWD: ALL uzasadnione (brak operatora), ew. ograniczone do konkretnych binarek agenty Straży.
- `-ac` na X serwerze — akceptowalne na smartfonie jednoużytkownikowym z profilem desktop; usunąć `-ac` i dodać `xauth` dla węzła z dostępem sieciowym innych procesów.
- bind `/sdcard` — ograniczyć do podkatalogu `NSIP`.
- polkit reguła `AUTH_ADMIN` dla `org.debian.apt.*` — miejsce na politykę (np. węzeł produkcyjny może wymagać autoryzacji przez SSH-klucz drugiego operatora).

## Najlepszy następny krok

Utworzyć `ZLECENIE_GLOWNE_PROOT_EDGE_INSTALLER_STRAZY.md` w `docs/AGENTY_PODWYKONAWCZE/` z kryteriami odbioru:
1. `install.sh` z profilami `--profile desktop|node-nsip|gateway`.
2. `lib/common.sh` z `install_pkg` raportującym rc.
3. Brak `glibc-repo`, brak VS Code z TUR; VS Code opcjonalnie w proot.
4. Idempotentność: ponowne uruchomienie nie psuje.
5. Runbook Phantom Killer w `docs/`.
6. Test na 2 realnych telefonach (Qualcomm + MediaTek).
7. **Profil desktop:** prawdziwe sudo z hasłem + polkit GUI (okno uprawnień dla Synaptic/GDebi/apt), D-Bus system bus + polkitd w `start-proot.sh`, agent autoryzacji w autostart DE, reguła `AUTH_ADMIN` dla `org.debian.apt.*`.
8. **Profil node-nsip:** sudo `NOPASSWD` jako uzasadniony brak-obsluga (brak operatora), brak DE/polkita.
9. **Główny cel:** smartfon jako komputer sterowniczy na Linuksie w proot — sterowniki/centrala NSIP żyją w proot, nie w Termuxie.
10. Weryfikacja polkit: `pkexec apt update` pyta o hasło admina, Synaptic uruchomiony z menu pokazuje okno autoryzacji, `dbus-send` zwraca listę usług system bus.
