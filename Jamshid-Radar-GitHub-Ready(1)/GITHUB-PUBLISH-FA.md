# آموزش انتشار جمشید روی GitHub

این بسته **مخزن GitHub را برای انتشار آماده می‌کند** اما آن را خودکار در حساب شما ایجاد نمی‌کند.

## ۱) ساخت مخزن

1. وارد https://github.com/new شو.
2. نام مخزن: `Jamshid-Network-Radar`
3. نوع: **Public** (برای GitHub Pages رایگان) یا طبق نیاز خودت Private با پلن سازگار.
4. اگر با Git مخزن موجود را Push می‌کنی، گزینه ساخت README یا `.gitignore` جدید را تیک نزن؛ این فایل‌ها در بسته موجود هستند.

## ۲) انتقال فایل‌ها با Git

پوشه `Jamshid-Network-Radar-GitHub` را از ZIP استخراج و وارد آن شو:

```bash
git init
git branch -M main
git add .
git commit -m "Initial JAMSHID v1.1 release and GitHub Pages"
git remote add origin https://github.com/ArioBarzanMoradi/Jamshid-Radar.git
git push -u origin main
```

`USERNAME` را با حساب GitHub خودت جایگزین کن. ورود به GitHub ممکن است از طریق GitHub CLI یا توکن/SSH نیاز باشد؛ پسورد معمول حساب GitHub به‌عنوان پسورد Git Push عمل نمی‌کند.

## ۳) فعال‌سازی صفحه وب

در مخزن، وارد **Settings → Pages** شو. در Build and deployment گزینه **Deploy from a branch** را انتخاب کن. Branch را `main` و Folder را `/docs` قرار بده و Save کن.

پس از انتشار، آدرس معمول سایت:

`https://USERNAME.github.io/Jamshid-Radar/`

به جای USERNAME نام حساب واقعی را وارد کن. لینک کد در سایت از همین آدرس حساب و نام مخزن به‌صورت خودکار ساخته می‌شود. راهنمای رسمی: https://docs.github.com/en/pages/getting-started-with-github-pages/configuring-a-publishing-source-for-your-github-pages-site

## ۴) نکات قبل از عمومی‌کردن

- فایل `config.example.json` فقط نمونه است. **فایل‌های واقعی پیکربندی، رمز عبور، کلید TLS یا VPN را Push نکن**.
- تصاویر داشبورد داخل این بسته **داده‌های آزمایشی** دارند؛ اطلاعات زنده سرور در آن‌ها نیست.
- مخزن در حال حاضر فایل LICENSE با مجوز Apache License 2.0 دارد.
- سایت GitHub Pages تنها برای معرفی جمشید است؛ **پنل مدیریتی واقعی** باید با HTTPS روی سرور Ubuntu خودت اجرا شود.

## ۵) استفاده روی Ubuntu

```bash
sudo apt update && sudo apt install -y git
git clone https://github.com/ArioBarzanMoradi/Jamshid-Radar.git
cd Jamshid-Radar
sudo bash scripts/install.sh
```

برای گرفتن گواهی SSL بعد از آماده‌بودن DNS و پورت 80:

```bash
sudo bash scripts/enable-ssl.sh jamshid.example.com
```

اگر قبلاً نسخه دیگری نصب شده است، از دستورهای ارتقا در `README.technical.md` استفاده کن؛ نصب‌کننده روی پیکربندی موجود بازنویسی نمی‌کند.

## ۶) پیشنهاد برای ظاهر مخزن

در بخش **About** مخزن این توضیح را قرار بده:

`JAMSHID — Self-hosted Ubuntu Network Radar for TCP/UDP ports, outbound connectivity and VPN service observability. Persian glass UI.`

موضوعات (*Topics*) پیشنهادی: `ubuntu`, `network-monitoring`, `fastapi`, `python`, `network-radar`, `vpn`, `self-hosted`, `persian-ui`.

اگر فایل‌ها را با گزینه **Add file → Upload files** در محیط وب می‌فرستی، محتویات پوشه استخراج‌شده را به **ریشه مخزن** ببر، نه داخل یک پوشه اضافی.
