<p align="center">
  <img src="ui/img/banner.png" alt="Nebula Studios" width="560">
</p>

<h1 align="center">Nebula Launcher</h1>

<p align="center">
  A free, non-commercial Minecraft: Java Edition launcher for the community servers of <b>Nebula Studios</b>.
</p>

---

## What it does

- **Microsoft sign-in only.** Players sign in with the Microsoft account that owns Minecraft: Java Edition. There is no offline or non-premium mode: accounts that don't own the game can't play.
- **One click to play.** For each server (project) the launcher installs the right Minecraft version, the Fabric loader, the Java runtime and the modpack, then starts the game connected to that server.
- **Clean, consistent installs.** Each project has its own game folder. Mods are checked against the modpack (SHA-1), and any extra `.jar` that isn't part of the project is removed before the game starts.
- **Server status.** Shows whether the server is open, how many players are online and the ping, using the same status ping as the in-game server list.

Our main project is **CraftTerra**, a modded survival server.

## Sign-in and privacy

Sign-in uses the standard flow — Microsoft OAuth (PKCE) → Xbox Live → XSTS → Minecraft Services — through the open-source library [minecraft-launcher-lib](https://codeberg.org/JakobDev/minecraft-launcher-lib). It is used only to get the player's profile and access token so the game can start with their own account.

- The refresh token is stored **only on the player's PC**, encrypted with Windows DPAPI (only the same Windows user can read it).
- Tokens are **never sent** to any server of ours.
- The launcher is **not monetized** and collects no data beyond what is needed to start the game.

## Running from source (Windows)

```bash
pip install -r requirements.txt
python nebula.py            # normal
python nebula.py --vista    # preview the main screen without signing in (Play still requires a real account)
```

Game files are stored in `%APPDATA%\.nebula`.

## Built with

- [minecraft-launcher-lib](https://codeberg.org/JakobDev/minecraft-launcher-lib) — installing and launching Minecraft, Microsoft sign-in
- [pywebview](https://pywebview.flowrl.com/) — the launcher window
- [Fabric](https://fabricmc.net/) — mod loader used by our modpacks

---

### En español

**Nebula Launcher** es el launcher gratuito de los servidores de **Nebula Studios** (como CraftTerra). Solo funciona con cuentas de Microsoft que tengan Minecraft: Java Edition comprado. Con un clic instala la versión, Fabric, Java y el modpack de cada proyecto y abre el juego. El token de inicio de sesión se guarda cifrado solo en tu PC y nunca se envía a nuestros servidores.

---

<sub>Not an official Minecraft product. Not approved by or associated with Mojang or Microsoft.</sub>
