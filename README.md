Poniżej są instrukcje jak zautomatyzować użycie skryptu patch_ubuntu_group.py używając systemd timer (czyli taka nowocześniejsza wersja cron).
Zasadnicza idea jest taka, żeby zdefiniować własną "usługę systemową", która zajmie się powtarzaniem wykonania skryptu.

***

### 1. Przygotowanie skryptu

Najpierw przenieś swój skrypt do standardowej lokalizacji dla lokalnych plików wykonywalnych i upewnij się, że ma odpowiednie uprawnienia.

```bash
sudo mv patch_ubuntu_group.py /usr/local/bin/susemgr-patch.py
sudo chmod +x /usr/local/bin/susemgr-patch.py
```

### 2. Utworzenie usługi systemd

Plik usługi mówi systemowi `systemd`, *jak* uruchomić Twój skrypt. 

Utwórz nowy plik w lokalizacji `/etc/systemd/system/susemgr-patch.service`:

```bash
sudo nano /etc/systemd/system/susemgr-patch.service
```

Dodaj następującą konfigurację:

```ini
[Unit]
Description=Patchowanie grupy serwerów Ubuntu w SUSE Manager
After=network-online.target
Wants=network-online.target

[Service]
Type=oneshot
# Użyj bezwzględnej ścieżki do Pythona i Twojego skryptu
ExecStart=/usr/bin/python3 /usr/local/bin/susemgr-patch.py

# Opcjonalne, ale zalecane: uruchom jako użytkownik bez uprawnień roota, jeśli wolisz
# User=twoj_uzytkownik
```

### 3. Utworzenie timera systemd

Plik timera mówi systemowi `systemd`, *kiedy* uruchomić powiązany plik usługi.

Utwórz nowy plik w lokalizacji `/etc/systemd/system/susemgr-patch.timer`:

```bash
sudo nano /etc/systemd/system/susemgr-patch.timer
```

Dodaj poniższą konfigurację. Ten przykład harmonogramuje uruchomienie na 1. dzień każdego miesiąca o 2:00 w nocy:

```ini
[Unit]
Description=Comiesięczne uruchamianie patchowania Ubuntu przez SUSE Manager

[Timer]
# Składnia: Rok-Miesiąc-Dzień Godzina:Minuta:Sekunda
OnCalendar=*-*-01 02:00:00

# Jeśli serwer będzie wyłączony w zaplanowanym czasie, wykonaj zadanie natychmiast po uruchomieniu systemu
Persistent=true

# Dodaj losowe opóźnienie (do 15 minut), aby zapobiec jednoczesnemu obciążeniu serwera, jeśli robi to wiele maszyn
RandomizedDelaySec=900 

[Install]
WantedBy=timers.target
```

### 4. Włączenie i uruchomienie timera

Teraz przeładuj demona `systemd`, aby zauważył Twoje nowe pliki, i włącz timer.

```bash
# Przeładuj systemd, aby rozpoznał nowe pliki jednostek
sudo systemctl daemon-reload

# Włącz timer, aby startował przy uruchomieniu systemu, i uruchom go od razu
sudo systemctl enable --now susemgr-patch.timer
```

### 5. Weryfikacja i logi

Możesz zweryfikować, czy Twój timer jest poprawnie zaplanowany, wyświetlając listę wszystkich aktywnych timerów:

```bash
systemctl list-timers | grep susemgr-patch
```

Ponieważ skrypt działa poprzez `systemd`, wszystkie komunikaty z funkcji `print()` w Twoim skrypcie Pythona zostaną automatycznie przechwycone przez dziennik systemowy. Po uruchomieniu skryptu możesz w dowolnej chwili sprawdzić jego wynik za pomocą komendy:

```bash
sudo journalctl -u susemgr-patch.service
```
