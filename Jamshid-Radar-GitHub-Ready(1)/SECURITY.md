# Security policy

If you discover a vulnerability in JAMSHID, please **do not publish sensitive exploit details or credentials in a public issue**. Use GitHub's *Report a vulnerability* / private vulnerability reporting feature if the repository owner enables it. Otherwise contact the maintainer privately via an appropriate channel stated on their profile.

Never open a public issue containing a deployed administrator password, `.env`, `/etc/network-radar/config.json`, private key, authentication cookie, target VPS credentials or a server IP you wish to keep confidential.

The app intentionally runs without root privileges and offers no remote command execution. For operational risks and limitations, see [technical notes](README.technical.md).
