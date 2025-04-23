# Discord Music Bot

Prosty bot muzyczny dla Discorda napisany w Pythonie przy użyciu biblioteki `discord.py`.

## Funkcje

*   Odtwarzanie muzyki z YouTube (pojedyncze utwory i playlisty).
*   Wyszukiwanie utworów na YouTube.
*   Kolejka utworów.
*   Podstawowe sterowanie odtwarzaniem (pauza, wznawianie, pomijanie).
*   Wyświetlanie listy utworów z playlisty.
*   Wybieranie konkretnego utworu z playlisty do dodania do kolejki.

## Komendy

Bot reaguje na prefiks `!` (można zmienić w `main.py`).

*   `!play <URL lub fraza>`: Odtwarza utwór lub playlistę z YouTube lub wyszukuje utwór.
*   `!search <fraza>`: Wyszukuje utwory na YouTube i pozwala wybrać jeden z listy.
*   `!next` lub `!skip`: Pomija aktualnie odtwarzany utwór.
*   `!pause`: Pauzuje odtwarzanie.
*   `!continue` lub `!resume`: Wznawia odtwarzanie.
*   `!disconnect` lub `!leave`: Rozłącza bota z kanału głosowego i czyści kolejkę.
*   `!list`: Wyświetla utwory z ostatnio załadowanej playlisty.
*   `!select <numer>`: Dodaje do kolejki utwór o podanym numerze z ostatnio załadowanej playlisty.
*   `!help`: Wyświetla pomoc (jeśli cog `help.py` jest załadowany).

## Instalacja

1.  **Sklonuj repozytorium:**
    ```bash
    git clone <URL_repozytorium>
    cd discord_bot
    ```
2.  **Utwórz i aktywuj środowisko wirtualne (zalecane):**
    ```bash
    python -m venv venv
    # Windows
    .\venv\Scripts\activate
    # Linux/macOS
    source venv/bin/activate
    ```
3.  **Zainstaluj zależności:**
    ```bash
    pip install -r requirements.txt
    ```
4.  **Zainstaluj FFmpeg:** Bot wymaga FFmpeg do przetwarzania audio. Pobierz go ze strony [ffmpeg.org](https://ffmpeg.org/download.html) i upewnij się, że jest dostępny w ścieżce systemowej (PATH) lub umieść `ffmpeg.exe` w głównym folderze bota.

## Konfiguracja

1.  Utwórz aplikację bota na [Discord Developer Portal](https://discord.com/developers/applications).
2.  Uzyskaj token bota.
3.  W pliku `config.py` wklej swój token w miejscu `TOKEN = "YOUR_BOT_TOKEN_HERE"`.

## Uruchomienie

```bash
python main.py
```

## Zależności

*   `discord.py`
*   `yt-dlp`
*   `PyNaCl` (dla obsługi głosu)
*   `ffmpeg` (wymagany zewnętrznie)

Zobacz plik `requirements.txt` po szczegóły.