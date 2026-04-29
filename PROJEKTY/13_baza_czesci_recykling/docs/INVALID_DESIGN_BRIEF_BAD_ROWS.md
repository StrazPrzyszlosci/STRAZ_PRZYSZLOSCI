# Invalid Design Brief — test negatywny

Ten brief celowo zawiera bledy w wierszach sekcji 6 i 7, ktore powinny byc wychwycone przez walidator.

---

## 1. Identyfikacja urzadzenia

| Pole | Wartosc |
|------|---------|
| brief_id | brief-invalid-test-01 |
| device_name | Testowe urzadzenie z bledami |
| device_purpose | Test negatywny walidacji |
| target_user | Tester |
| project_context | test-context |

---

## 2. Funkcja urzadzenia

| Pole | Wartosc |
|------|---------|
| primary_function | Testowanie walidacji wierszy |
| secondary_functions | Brak |
| inputs | 1x I2C sensor, 1x SPI display |
| outputs | 1x UART telemetry |
| communication_interfaces | UART |

---

## 3. Zasilanie

| Pole | Wartosc |
|------|---------|
| power_source | USB 5V |
| voltage_levels | 3.3V |
| max_current_draw | 100mA |
| power_constraints | Brak |

---

## 4. Srodowisko pracy

| Pole | Wartosc |
|------|---------|
| operating_environment | indoor |
| temperature_range | 0C do 50C |
| humidity_range | 10-80% RH |
| mechanical_constraints | Brak |
| emc_requirements | Brak |

---

## 5. Ograniczenia kosztowe

| Pole | Wartosc |
|------|---------|
| max_bom_cost | 30 PLN |
| reuse_priority | reuse_first |
| budget_notes | Test |

---

## 6. Reuse parts — preferencje z katalogu

### 6.1 Czesci z kanonicznego katalogu (data/parts_master.jsonl)

| part_slug | Ilosc | Uwagi |
|-----------|-------|-------|
| __DO_UZUPELNIENIA__ | TBD | placeholder |
| BAD SLUG!!! | zero | zly slug i zla ilosc |
| valid-slug | 3 | OK |

### 6.2 Czesci spoza katalogu (missing parts)

| Funkcja | Wymagany parametr | Czy da sie pozyskac z donor board? | Uwagi |
|---------|------------------|-----------------------------------|-------|
| __DO_UZUPELNIENIA__ | TBD | MOZE | placeholder i zla wartosc donor |
| NTC sensor | | TAK | brak wymaganego parametru |

---

## 7. Zalozenia i ograniczenia projektowe

| Pole | Wartosc |
|------|---------|
| assumptions | Jeden. |
| constraints | x |
| known_risks | Brak |
| compliance | Brak |

---

## 8. Donor board profile

| Pole | Wartosc |
|------|---------|
| target_board | Nie dotyczy |
| board_capabilities | Nie dotyczy |
| flash_method | UART |
