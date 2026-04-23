# Architektura Onboardingu

## Cel dokumentu

Ten dokument rozdziela dwa różne procesy wejścia do ekosystemu **Straży Przyszłości / Narodowych Sił Intelektualnych**. To rozróżnienie jest ważne, bo nie każda osoba wchodząca do inicjatywy chce od razu zostać providerem danych, a nie każdy provider musi przechodzić przez tę samą ścieżkę co nowy Strażnik.

## Dwa osobne onboardingi

W projekcie funkcjonują dwa niezależne, ale powiązane procesy:

1. **Onboarding Strażnika**
   Pierwsze wejście nowej osoby do inicjatywy. Jego celem jest rozpoznanie pasji, kompetencji, zasobów i czasu danej osoby oraz skierowanie jej do odpowiednich sekcji repozytorium i pierwszych zadań.
2. **Onboarding providera danych**
   Techniczne wejście do wspólnego API dla węzłów pomiarowych, starych smartfonów, gospodarstw, partnerów zewnętrznych i projektów społecznościowych, które chcą dostarczać dane lub odbierać wyniki analityczne.

Te dwa onboardingi nie powinny być mieszane w jednej instrukcji, jednym formularzu ani jednym komunikacie na stronie.

## Onboarding Strażnika

Onboarding Strażnika powinien być realizowany na **zewnętrznej stronie inicjatywy** jako ankieta i rekomendator zadań.

Ta ścieżka musi być zaprojektowana w sposób merytokratyczny również wobec osób, które nie mają klasycznej pozycji zawodowej, ale potrafią skutecznie pracować z pomocą nowoczesnych narzędzi agentowych i generatywnych, takich jak `Codex`. Jeżeli ktoś umie osiągać realne cele, łączyć zasoby, adaptować kod i dowozić efekty, powinien być traktowany jako pełnoprawny współtwórca sieci intelektualnej, a nie jako uczestnik drugiej kategorii.

Jego rola:

- przyjąć zgłoszenie osoby, która chce włączyć się do inicjatywy po raz pierwszy,
- rozpoznać obszar pasji i typ wkładu, jaki dana osoba chce wnieść,
- skierować tę osobę do właściwej sekcji tego repozytorium,
- zaproponować pierwsze dokumenty, pierwsze projekty i pierwsze Issues.

Dla ścieżki wolontariusza z agentem to nadal za mało. Taki onboarding powinien kończyć się nie tylko listą dokumentów, ale też **gotowym przydziałem wolontariackim**, który lokalny agent może od razu przejąć i poprowadzić bez wymuszania, by człowiek pisał od zera własny brief.

Kanoniczny plik dla tej warstwy jest utrzymywany tutaj:

- [Wolontariusze: gotowe przydziały](WOLONTARIUSZE_GOTOWE_PRZYDZIALY.md)

Minimalne dane wejściowe dla rekomendatora:

- pasje i obszary zainteresowań,
- kompetencje techniczne lub organizacyjne,
- sposób pracy i używane narzędzia, także narzędzia AI-native,
- dostępny czas,
- dostępne zasoby, na przykład stary smartfon, ESP32, czujniki, kamera, wiedza domenowa,
- dostępne zasoby obliczeniowe, na przykład konto `Kaggle`, `Colab`, lokalny GPU albo możliwość uruchamiania notebooków,
- preferowany rodzaj wkładu: kod, hardware, dokumentacja, analiza, marketing, badania, provider danych.

Warto przy tym jasno komunikować, że brak własnego urządzenia pomiarowego nie wyklucza realnego wejścia do projektu. Jeżeli dane są dostarczane przez providerów i społeczność przez wspólne API, nowy Strażnik może od początku wejść w architekturę danych, adaptery, analizę, dokumentację i budowę bazy wiedzy. Przykład takiego modelu opisuje dokument:

- [Przykłady Gotowego Kodu i Otwartych Wzorców](PRZYKLADY_GOTOWEGO_KODU.md)

Minimalne dane wyjściowe rekomendatora:

- rekomendowana ścieżka wejścia,
- lista dokumentów startowych,
- lista projektów do przeczytania,
- lista pierwszych zadań lub Issues,
- gotowy przydział wolontariacki dobrany do dostępnych zasobów, jeżeli dana osoba wchodzi z lokalnym agentem,
- wskazanie, czy dana osoba nadaje się do uruchamiania autonomicznych notebooków badawczych na własnych zasobach,
- wskazanie, czy dana osoba nadaje się do zadań `resource scoutingu`, czyli rozpoznawania nowych klas zasobów możliwych do uruchomienia przez inicjatywę,
- wskazanie, czy dana osoba powinna przejść dalej do onboardingu providera.

Ważny wariant tej ścieżki to **wolontariusz z agentami AI i kontem Kaggle/Colab**. Taka osoba może nie mieć własnego hardware terenowego, a mimo to wnosić bardzo realny wkład:

- uruchamiać autonomiczne notebooki przygotowane przez inicjatywę,
- zużywać własne darmowe tokeny i limity obliczeniowe na rzecz wspólnego celu,
- zapisywać wyniki do własnego forka,
- przekazywać je do głównego repozytorium przez `Pull Request`,
- działać jako rozproszony węzeł wykonawczy dla zadań discovery, enrichment i research.

To powinno być komunikowane wprost jako pełnoprawna ścieżka wejścia do inicjatywy.

Ważne rozróżnienie organizacyjne:

- wolontariusz z agentem powinien być kierowany do `docs/WOLONTARIUSZE_GOTOWE_PRZYDZIALY.md`,
- `docs/AGENTY_PODWYKONAWCZE/` nie jest onboardingiem wolontariackim, tylko wewnętrznym katalogiem zleceń dla agentów operatora repo przy obecnym braku wolontariuszy.

Równolegle warto przewidzieć wariant **wolontariusza-resource scouta**. Taka osoba może wnosić wkład przez:

- wskazywanie nowych klas zasobów, które AI powinno analizować,
- rozpoznawanie lokalnych źródeł sprzętu, danych, energii albo mocy obliczeniowej,
- testowanie, czy dany zasób da się włączyć do kolejnych łańcuchów automatyzacji,
- dokumentowanie ograniczeń, kosztów wejścia i potencjału rozwojowego.

## Onboarding providera danych

Onboarding providera jest procesem technicznym i operacyjnym. Dotyczy tylko tych osób, zespołów i węzłów, które chcą zasilać wspólne API danymi albo odbierać wyniki analityczne jako uczestnicy warstwy integracyjnej.

Ta ścieżka obejmuje między innymi:

- zapoznanie się z kontraktem `v1`,
- mapowanie danych do wspólnego schematu,
- rejestrację providera,
- odbiór `write_token`,
- przesyłanie obserwacji i zdarzeń,
- utrzymanie jakości danych,
- ewentualną rotację tokenu i proces odzyskiwania dostępu.

Szczegóły tej ścieżki opisuje dokument:

- [Jak Zostać Dostawcą Danych](JAK_ZOSTAC_DOSTAWCA_DANYCH.md)

## Punkt styku obu ścieżek

Najważniejsza zasada brzmi: **nie każdy Strażnik jest providerem, ale każdy provider może być Strażnikiem**.

W praktyce oznacza to:

- nowa osoba może wejść do inicjatywy tylko jako analityk, dokumentalista, autor modeli, hardware hacker albo organizator,
- dopiero później może zdecydować, że chce budować własny węzeł pomiarowy i zostać providerem,
- onboarding Strażnika ma pomóc odkryć najlepszy pierwszy wkład,
- onboarding providera ma dopiero uruchomić bezpieczną ścieżkę techniczną do API.

## Integracja ze stroną inicjatywy

Repozytorium strony inicjatywy powinno utrzymywać **ankietę i rekomendator zadań**, ale nie powinno duplikować całej wiedzy z tego repozytorium. Strona zewnętrzna ma być warstwą wejścia, a to repozytorium pozostaje źródłem prawdy dla treści merytorycznej i zadań.

Dlatego rekomendator powinien:

- korzystać z katalogu rekomendacji utrzymywanego w tym repozytorium,
- przekierowywać użytkownika do właściwych dokumentów, projektów i szablonów Issue,
- umieć wskazać kanoniczny plik gotowych przydziałów wolontariackich dla ścieżki AI-native,
- rozróżniać ścieżkę ogólnego zaangażowania od ścieżki providera danych.

Kanoniczny katalog dla tej warstwy jest utrzymywany tutaj:

- [Katalog rekomendatora zadań Strażnika](../data/onboarding/straznik_rekomendator_v1.json)

## Artefakty repozytorium

Aktualna warstwa onboardingowa w repozytorium obejmuje:

- [Architektura Onboardingu](ARCHITEKTURA_ONBOARDINGU.md)
- [Wolontariusze: gotowe przydziały](WOLONTARIUSZE_GOTOWE_PRZYDZIALY.md)
- [Jak Zostać Dostawcą Danych](JAK_ZOSTAC_DOSTAWCA_DANYCH.md)
- [Nowy Strażnik / pierwsze zaangażowanie](../.github/ISSUE_TEMPLATE/nowy_straznik.md)
- [Pomysł / propozycja rozwiązania](../.github/ISSUE_TEMPLATE/pomysl_rozwiazanie.md)
- [Zastrzeżenie / uwaga / ryzyko](../.github/ISSUE_TEMPLATE/zastrzezenie_uwaga.md)
- [Nowy provider danych / węzeł pomiarowy](../.github/ISSUE_TEMPLATE/provider_danych.md)
- [Katalog rekomendatora zadań Strażnika](../data/onboarding/straznik_rekomendator_v1.json)

## Szybki kanał mobilny

Strona inicjatywy powinna umożliwiać także bardzo prosty kanał wejścia z telefonu. Chodzi o sytuację, w której ktoś:

- wpisuje pomysł ręcznie na smartfonie,
- dyktuje go przez `Gboard` lub inny mechanizm mowy na tekst,
- chce od razu zapisać go do repozytorium w formie `Issue`.

Dlatego poza onboardingiem Strażnika i onboardingiem providera potrzebny jest trzeci, bardzo krótki tor wejścia:

- `Zgłoś pomysł`
- `Zgłoś zastrzeżenie`

Ten kanał nie zastępuje pełnego onboardingu, ale pozwala szybko złapać cenne obserwacje, pomysły i ryzyka zanim znikną.

Najprostszy wariant tego toru powinien prowadzić bezpośrednio do gotowych `Issue template` z poziomu strony inicjatywy. To jest rozwiązanie najtańsze, najprostsze i wystarczające dla wersji podstawowej.

Dopiero jako kolejny etap można utrzymywać most komunikatorowy, na przykład:

- `Telegram -> Cloudflare Worker -> GitHub Issues`
- `WhatsApp -> Cloudflare Worker -> GitHub Issues`

Szczegóły tej architektury opisuje dokument:

- [Architektura mostu Telegram -> GitHub Issues](ARCHITEKTURA_MOSTU_TELEGRAM_GITHUB_ISSUES.md)
- [Architektura mostu WhatsApp -> GitHub Issues](ARCHITEKTURA_MOSTU_WHATSAPP_GITHUB_ISSUES.md)

## Kryteria sukcesu

Onboarding jest zaprojektowany poprawnie, gdy:

- nowa osoba nie trafia od razu do technicznej dokumentacji API bez kontekstu,
- strona zewnętrzna potrafi skierować Strażnika do konkretnego projektu i pierwszego zadania,
- provider danych ma osobną, czytelną ścieżkę techniczną,
- oba procesy są ze sobą kompatybilne, ale nie są mylone,
- repozytorium pozostaje źródłem prawdy dla zadań, dokumentów i standardów.
