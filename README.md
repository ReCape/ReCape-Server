# ReCape Server
## What is this?
It's the codebase that runs the ReCape servers.

## What is it made of?
It's a Python program that consists of two Flask servers, two databases (plus a folder), and a Minecraft server.

## How do I run it?
- Download the code to the computer you'll be running the server on
- Install the dependencies (possibly incomplete list in deps.txt)
- Add Spigot server to root directory, named server.jar (1.20.2 from getbukkit.org)
- Add your SSL certificates as ssl/doain.cert.pem and ssl/private.key.pem
- Run start.py
- Optional: Set up a system (depending on your operating system) to run the server on computer startup

### Windows Disclaimer
This project cannot be ran under Windows regularly. You can still use it by enabling debug mode, enabling an alternate server that will work on Windows. DO NOT USE DEBUG MODE IN PRODUCTION!

## How do I edit it?
You can head in and edit the code files directly. If you create a file named .debug in the same directory as the server, the server will run in debug mode and will use the builtin Flask debug server, as well as targeting the Localhost URL.
