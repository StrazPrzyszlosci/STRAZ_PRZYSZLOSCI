# Runbook: Phantom Process Killer (Android 13+)

Android 13+ ma mechanizm "Phantom Process Killer" — ubija długie procesy w tle (np. proot), powodując `Process completed (signal 9)` po kilku minutach. To **najczęstsza przyczyna padania** proot na starych smartfonach.

## Symptomy

- proot pada z `signal 9` po ok. 3-10 minutach pracy.
- VNC/Termux-X11 zrywa sesję bez ostrzeżenia.
- `dmesg` / logcat pokazuje `ActivityManager: killing phantom process`.

## Rozwiązanie (jednorazowo przez ADB z PC)

Wymaga podłączenia telefonu do PC z włączonym USB debugging i zainstalowanym `adb`.

```bash
# Podnieś limit procesów phantom do max (int32)
adb shell "/system/bin/device_config put activity_manager max_phantom_processes 2147483647"
# Potwierdź wartość
adb shell "/system/bin/device_config get activity_manager max_phantom_processes"
```

Powinno zwrócić `2147483647` (lub maksymalną wartość int32).

## Rozwiązanie (per-aplikacja, GUI — bez ADB po restarcie)

Dla nowszych Androidów:

1. Ustawienia → Opcje Programisty
2. „Maksymalna liczba procesów w tle" / „Phantom process limit"
3. Ustaw na najwyższą wartość lub wyłącz ograniczenie.
4. Ponadto: w Ustawieniach aplikacji Termux → Bateria → "Bez ograniczeń" / "Bez optymalizacji".

## Weryfikacja (po fix)

W Termux uruchom:

```bash
# Test długotrwały — jeśli przeżyje >10 min, fix działa
yes > /dev/null &     # obciąża CPU, trzyma proces przy życiu
sleep 600
kill %1
```

## Alternatywa: Termux:Boot + wznawianie

Jeśli Phantom Killer mimo limitu ubija sesję, użyj `Termux:Boot` do auto-wznowienia serwisu proot po restarcie telefonu:

1. Zainstaluj Termux:Boot z F-Droid.
2. Utwórz `~/.termux/boot/start-straz.sh`:
   ```bash
   #!/data/data/com.termux/files/usr/bin/bash
   termux-wake-lock
   bash ~/start-proot.sh &
   ```
3. Telefon po restarcie auto-podniesie węzeł.

## Notatki

- Te ustawienia **nie przeżywają reboot** na niektórych ROM-ach — wtedy trzeba powtórzyć `adb shell device_config` po restarcie.
- Termux powinien być wykonkludowany z optymalizacji baterii (Ustawienia → Bateria → Termux → Bez ograniczeń).
- `termux-wake-lock` zapobiega usypiania CPU — zalecany w skryptach startowych węzła.
