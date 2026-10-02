[![English](https://img.shields.io/badge/README-English-24292f?style=for-the-badge)](./README.md) [![한국어](https://img.shields.io/badge/README-%ED%95%9C%EA%B5%AD%EC%96%B4-24292f?style=for-the-badge)](./README.ko.md)

# JP Play — Downloader for Region-Limited Apps

A PC tool for downloading Japanese and other region-limited Android apps that may not appear in the Korean Play Store, then installing them on a phone over USB.

## Run

Double-click `run.bat` (or run `python jpplay.py`). On first use, required tools such as `apkeep` and `adb` are downloaded automatically into `tools/`.

## Usage

1. **Find an app**: enter the app name, choose a country such as JP, and click "Search on Web". The Japanese Play Store opens in your browser.
2. **Download**: paste the app-page URL (`...details?id=jp.xxx`) and click "Download". Files are saved under `downloads/`.
   - **APKPure**: can download without signing in and carries many Japanese apps.
   - **Google Play**: downloads the official package. A Google account email and AAS token are required.
3. **Install**: enable Developer options → USB debugging on the phone, connect it to the PC, then click "Check Connected Device". Approve the authorization prompt on the phone and install. Both `.apk` and `.xapk` (split APK + OBB) are supported.

### Getting a Google Play AAS Token (Optional)

1. Sign in at https://accounts.google.com/EmbeddedSetup in a PC browser.
2. Open Developer Tools (F12) → Application → Cookies and copy the `oauth_token` value.
3. Run:
   `tools\apkeep.exe -e EMAIL --oauth-token COPIED_VALUE -d google-play -a com.android.chrome downloads`
4. Enter the resulting AAS token in the program. Treat the token like a password.

## Phone-Only Option

If you want an "all-country Play Store" experience directly on your phone without a PC, consider **Aurora Store**, an open-source Play Store client.

- Install from https://auroraoss.com or F-Droid
- Sign in anonymously, connect to a Japanese VPN, then search and install Japanese apps directly

## Notes

- The official Play Store app itself cannot simply be modified. It is Google-signed, and region availability is determined by Google servers using account/payment-country and IP signals. This tool and Aurora Store take a different client-side approach.
- Some Japanese apps, including banking, PayPay, or games, may still require a Japanese IP address or Japanese phone number after installation.
- Updates are not automatic. Download and install the package again when needed. Aurora Store supports update checks.
