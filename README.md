# CAP-Server
A CAP server that clones the IPAWS style of servers, sutible for many ENDECs on the market for testing.

I do not suggest to use this for actual public safety, and I am not liable for damages.

Please note, generate signing keys and certs, read the code for the passphrase + the filenames.

Make sure to start WebServer.py and alert_processor.py for functionality.

## Features Added From Original
- CAP alerts now auto expire properly and get removed from the feed, emulating the IPAWS server style exactly.
- Pulls alert dictionaries from EAS2Text (requires my custom version of EAS2Text located [here](https://github.com/Newton-Communications/E2T/tree/nwr-localities))
- Allows for translation of ZCZC headers and specifying custom start and end times for the ability to use this with ASMARA as a CAP Translation Server.
- CAP Sending keys have been added which allow for the send endpoint to be secured properly, rather than an open endpoint like before.


## Bug Fixes
- CAP certificates now verify properly on a DASDEC II with custom OpenSSL version compiled on Fedora 10.
- Media folder now works and functions properly.
- CAP pins have been properly implemented and the whole server (all endpoints) now require a PIN as originally intended by IPAWS.
- TTS bugs have been fixed.

###### Copyright © 2024 SecludedFox Systems
