# River Classic configuration

This directory contains the hand-configured parts of my River Classic desktop
and related command-line environment. It is **not** intended to document or
restore every application that happens to write files under `~/.config`.

The current system is Fedora 44 KDE Plasma Edition. Package names and commands
below use Fedora's `dnf`; names may differ on another distribution.

## What is configured

| Component | Configuration | Purpose |
|---|---|---|
| River Classic / rivertile | `river/` | Session startup, bindings, rules, input, tags and gapless tiling |
| Waybar | `waybar/` | Per-output tags, status modules and custom desktop panels |
| Mako | `mako/` | Notifications, history and do-not-disturb mode |
| Kanshi | `kanshi/` | Docked and laptop-only monitor profiles |
| Foot | `foot/` | Terminal fonts, sizing, scrollback and colours |
| Fuzzel | `fuzzel/` | Application launcher |
| gtklock / swaylock | `gtklock/`, `swaylock/` | Styled lock screen and fallback |
| Fusuma | `fusuma/` | Three-finger tag switching gestures |
| XDG portals | `xdg-desktop-portal/` | GTK generic portals, wlr screenshots/casting, KWallet secrets |
| systemd user target | `systemd/user/river-session.target` | Marks River as the active graphical session |
| tmux | `tmux/` | Wayland clipboard, sessions, panes, popups and matching theme |
| Neovim | `nvim/` | IDE-like editing, LSP, formatters, Git integration and matching theme |
| Doom Emacs | `doom/`, `desktop-entries/emacs.desktop` | Editor modules, titleless PGTK frames and daemon-backed clients |
| GTK/KDE appearance | `gtk-3.0/`, `gtk-4.0/`, `kdeglobals` | Consistent Breeze Dark application appearance |

The shared palette is dark blue-black (`#08111F`) with gold (`#D6AE4A`), sea
blue (`#79AFC7`), red (`#B94747`) and green (`#5F9C83`) accents.

## Install the packages

Enable whatever repository supplies `river-classic` on the target Fedora
release first. On this machine that package supplies `river`, `riverctl` and
`rivertile`.

Install the core desktop and helper packages:

```sh
sudo dnf install \
  river-classic waybar mako kanshi foot fuzzel \
  swaybg swayidle swaylock gtklock wlopm wlsunset \
  tuned tuned-ppd \
  xdg-desktop-portal xdg-desktop-portal-gtk xdg-desktop-portal-wlr \
  polkit-kde kf6-kwallet qt6-qtwayland qt5ct qt6ct \
  network-manager-applet nm-connection-editor blueman udiskie \
  pipewire wireplumber pavucontrol playerctl \
  wl-clipboard cliphist brightnessctl ddcutil \
  grim slurp swappy libnotify \
  python3-gobject gtk-layer-shell \
  breeze-icon-theme breeze-gtk-gtk3 breeze-gtk-gtk4 \
  google-noto-sans-fonts google-noto-sans-sinhala-fonts \
  google-noto-color-emoji-fonts \
  tmux fzf neovim emacs-pgtk ripgrep fd-find git
```

Foot is configured to prefer the **Hack** font. Install a Fedora Hack font
package if it is not already present, or change `font=` in `foot/foot.ini`.

Some items are optional:

- `ddcutil` is needed only for controlling an external monitor over DDC/CI.
- `gtklock` provides the full date/time lock screen; `swaylock` is the fallback.
- NetworkManager, Blueman and udiskie provide the tray applets.
- `network-manager-applet` supplies `nm-applet`; Fedora's
  `nm-connection-editor` package supplies the graphical connection editor used
  when the Waybar network module is clicked.
- `qt5ct` and `qt6ct` are useful fallback configuration tools for Qt 5 and Qt 6
  applications. The current River session primarily uses KDE's platform theme
  (`QT_QPA_PLATFORMTHEME=kde`), so it does not force either qtct backend.
- `grim`, `slurp` and `swappy` provide full-screen, region and annotated shots.
- `playerctl` provides the media-key bindings.

### Fusuma

Fusuma was installed as a Ruby gem on this machine:

```sh
sudo dnf install ruby rubygems libinput
sudo gem install fusuma
```

Do **not** add the user to the broad `input` group. Install the included udev
rule instead; it grants the active local session access to touchpads only:

```sh
sudo install -o root -g root -m 0644 \
  ~/.config/river/70-touchpad-uaccess.rules \
  /etc/udev/rules.d/70-touchpad-uaccess.rules
sudo udevadm control --reload-rules
sudo udevadm trigger --subsystem-match=input --action=change
```

Log out and back in, then check that `fusuma --list-devices` sees the touchpad.
The Fusuma filter currently names `MSFT0001:00 04F3:31BE Touchpad`; update
`fusuma/config.yml` when restoring onto different hardware.

## Restore the configuration

Place this configuration tree at `~/.config`. Preserve executable bits on the
scripts in `river/`, `waybar/` and `tmux/`. Then reload the user systemd manager:

```sh
systemctl --user daemon-reload
```

The River init exports the Wayland desktop environment to D-Bus and systemd,
then starts `river-session.target`. That target pulls in
`graphical-session.target`. Do not manually start the generic target or either
portal service from `river/init`; D-Bus/systemd activates portals after the
session environment has been imported.

The River-only processes—Waybar, Mako, Kanshi, Fusuma and the other applets—are
started by `river/init`, not as always-running user services. This prevents
them from also appearing in Plasma.

## Hardware-specific changes

Review these before using the configuration on another computer:

- `kanshi/config`: output names, resolutions and positions. Current outputs are
  `HDMI-A-1` and `eDP-1`, both at 1920×1080.
- `river/scripts/brightness` and `waybar/config`: laptop backlight device is
  `amdgpu_bl1`.
- `waybar/scripts/brightness-panel.py`: the external display selector is
  manufacturer `GSM`, model `RDS-220L`.
- `waybar/config`: battery notifications read `BAT0`.
- `fusuma/config.yml`: exact touchpad name.

Useful discovery commands are:

```sh
riverctl list-outputs
brightnessctl --list
ddcutil detect
ls /sys/class/power_supply
fusuma --list-devices
```

For external brightness, enable DDC/CI in the monitor's on-screen menu. Some
hardware may also require access to the relevant I²C device.

## Custom Wayland helpers

`river/bin/river-cycle-tags` is a small locally written Wayland client, not a
downloaded utility. Waybar wheel scrolling and Fusuma gestures both call it to
move between tags on the focused output.

`river/bin/river-idle-inhibitor` is another small local client. It creates an
invisible, pointer-transparent Wayland surface and attaches the standard idle
inhibit protocol to it while `Keep awake` is enabled in quick settings. This
lets the popup replace Waybar's otherwise inaccessible built-in idle-inhibitor
module.

The compiled binaries are included. To rebuild them:

```sh
sudo dnf install gcc pkgconf-pkg-config wayland-devel
~/.config/river/native/river-cycle-tags/build
~/.config/river/native/idle-inhibitor/build
```

Their source and protocol XML files are under `river/native/`.

## Waybar integrations

The compact bar keeps River tags and title, clock, volume, battery, keyboard
layout, clipboard history and the system tray visible. `WIN` appears only in
global floating mode. Less frequently used controls are grouped under `SYS`.

The custom panels are GTK 3 layer-shell programs:

- `desktop-panel.py` shows Mako history and clipboard history without Fuzzel.
  It can dismiss/restore notifications, toggle DND, select clipboard entries
  and wipe clipboard history.
- `brightness-panel.py` shows the laptop slider and, when connected, a second
  DDC/CI slider for the external monitor.
- `quick-settings.py` provides the `SYS` popup: layout mode, night light, idle
  inhibition, microphone and DND toggles; brightness sliders; notification,
  network, Bluetooth and audio shortcuts; screenshot controls; and confirmed
  session/power actions. It also controls the standard Power Profiles D-Bus
  API exposed by Fedora's system-wide `tuned-ppd` service.
  It closes only when the transparent area outside it is clicked, not when the
  pointer merely leaves it. `SYS` turns gold for DND/idle
  inhibition and red while the microphone is active.
- `night-light` controls `wlsunset` and exposes its state to Waybar.
- `keyboard-layout` switches between US English and Sinhala phonetic and uses
  Right Ctrl as the Compose key. It resets to US when River starts and before
  the lock screen opens.
- `layout-mode` toggles every connected output between rivertile and River's
  floating fallback. `Super+Shift+Space` performs the same toggle, and Kanshi
  reapplies the current mode after docking or undocking. Windows explicitly
  floated by a rule or by moving/resizing them remain floating when tiled mode
  returns; `Super+Space` toggles an individual window back into the layout.
  Focus follows the pointer in tiled mode and changes only on a click or an
  explicit focus command in floating mode.
- `window-controls.py` adds a `WIN` button while global floating mode is active.
  Its touch-friendly panel can select, move, resize, snap, close, float/tile or
  fullscreen the focused window, or send it to another monitor and follow it.
  The panel does not replace River's focused view, so its commands continue to
  target the application. It and the other GTK panels use the same outside-click
  dismissal.
- `microphone-status` reports and toggles the PipeWire default source.
- `power-menu` offers lock, suspend, logout, reboot and power off.

Volume and microphone commands use `wpctl`, so PipeWire and WirePlumber must be
running. Clipboard history requires both `wl-clipboard` and `cliphist`.

Screenshots use the shared `river/scripts/screenshot` helper from both the
keyboard and `SYS`: `Print` captures all outputs, `Super+Print` selects and
saves a region, and `Super+Shift+Print` selects a region for annotation in
Swappy. Captures are saved under `~/Pictures/Screenshots`.

## Portals and KWallet

`xdg-desktop-portal/river-portals.conf` selects:

- GTK for generic interfaces such as file selection;
- wlr for screenshots and screen casting;
- KWallet for the Secret portal.

Do not add `xdg-desktop-portal` or `xdg-desktop-portal-wlr` to River autostart.

Brave Origin is launched through `~/.local/bin/brave-kwallet`, which is outside
this configuration directory and therefore must be recreated separately:

```sh
mkdir -p ~/.local/bin
printf '%s\n' '#!/bin/sh' \
  'exec /usr/bin/brave-origin-stable --password-store=kwallet6 "$@"' \
  > ~/.local/bin/brave-kwallet
chmod 0755 ~/.local/bin/brave-kwallet
```

This assumes `brave-origin-stable` has already been installed from its own
package source.

## Idle, locking and power

The configured River session:

1. locks after 10 minutes idle;
2. powers displays off through `wlopm` after 15 minutes;
3. suspends on battery after 30 minutes;
4. suspends on either power source after 60 minutes;
5. locks before system sleep.

Lid-close suspend remains logind/system policy; locking the screen does not
prevent it. Waybar's idle inhibitor prevents the `swayidle` timeouts while it
is enabled.

## Foot and tmux

Foot uses Hack 10.5, Noto Color Emoji fallback, 10,000 lines of scrollback,
Wayland URL launching and the shared colour palette. Command history and arrow
key behavior are provided by the shell, not by Foot.

tmux uses its normal `Ctrl-b` prefix. It enables mouse support, vi copy mode,
Wayland clipboard copying through `wl-copy`, current-directory splits, popup
shell/session selection and themed status lines. The FZF session picker needs
`fzf`. See comments in `tmux/tmux.conf` for the custom bindings.

## Neovim IDE

This configuration requires Neovim 0.12 or newer because it uses the native
`vim.pack` plugin manager. On first launch it fetches the pinned plugins listed
in `nvim/nvim-pack-lock.json`. Use `:PackUpdate` to review updates.

Configured language servers cover Bash, C/C++, CSS, Go, HTML, JavaScript,
TypeScript, JSON, Lua, Python, Rust and YAML. Mason installs the non-C servers,
plus Prettier, Ruff, shfmt and StyLua. Install Clangd separately:

```sh
sudo dnf install clang-tools-extra
```

Go formatting uses `gofmt`, and Rust formatting/checking uses `rustfmt` and
`clippy`; install the Go and Rust toolchains when those languages are needed.
Full custom bindings are documented in `nvim/KEYMAPS.md`. Inside Neovim,
`Space` also opens the which-key guide.

## Doom Emacs

Fedora's packaged `emacs.service` keeps one PGTK Emacs daemon in the user
session. Graphical clients use the session's native Wayland display. Fuzzel and
application launchers use the included desktop-entry override; the `ec` and
`et` Zsh aliases open graphical and terminal clients. The aliases ask systemd
to start the service first, so they cannot race a fallback daemon.

River's `Super+E` binding also starts the service if necessary and opens a new
graphical Emacs client frame.

Install the launcher override and enable the packaged user service with:

```sh
install -Dm0644 ~/.config/desktop-entries/emacs.desktop \
  ~/.local/share/applications/emacs.desktop
systemctl --user enable --now emacs.service
```

No custom Emacs service or service override is required.

Keep `doom/snippets/` present for personal YASnippet templates. Doom supplies
its own language snippets; this directory is where local additions belong:

```sh
mkdir -p ~/.config/doom/snippets
```

Python completion and diagnostics use `basedpyright`; JavaScript and
TypeScript use `typescript-language-server`. Install them into the existing
user-local executable path with:

```sh
pipx install basedpyright
npm install --global --prefix ~/.local typescript@5 typescript-language-server
```

Run `doom sync` after changing `doom/init.el`. Doom's Tree-sitter grammars are
installed on demand when a supported language is first opened.

## Quick validation

Run these after restoring:

```sh
sh -n ~/.config/river/init
sh -n ~/.config/river/scripts/* ~/.config/waybar/scripts/night-light \
  ~/.config/waybar/scripts/keyboard-layout ~/.config/waybar/scripts/power-menu
python3 -m py_compile ~/.config/waybar/scripts/*.py
fusuma --show-config
waybar --version
mako --version
```

Finally, log into River and test portals from a Flatpak or a browser screen-share
dialog, test both brightness controls, and confirm that Waybar tags are
independent on each output.
