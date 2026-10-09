# Neovim key map

The leader key is `Space`. Pause briefly after pressing it to open the
which-key guide.

## Home screen

The home screen appears only when Neovim starts without a file. Number keys
open the listed recent files directly.

| Key | Action |
|---|---|
| `1`–`5` | Open the corresponding recent file |
| `f` | Find files |
| `g` | Search text in the current project |
| `r` | Show all recent files |
| `e` | Open the file explorer |
| `n` | Create an empty buffer |
| `c` | Edit this Neovim configuration |
| `m` | Open Mason tool management |
| `k` | Search all key maps |
| `h` | Search help |
| `q` | Quit |

## Everyday editing

| Key | Action |
|---|---|
| `Ctrl-s` | Save |
| `Space w` | Save |
| `Space q` | Close window |
| `Space Q` | Quit Neovim |
| `Shift-h` / `Shift-l` | Previous / next buffer |
| `Space b d` | Delete buffer |
| `Alt-j` / `Alt-k` | Move line or selection |
| `Ctrl-h/j/k/l` | Move through Neovim splits and tmux panes |
| `Space t t` | Open a terminal split |
| `Esc Esc` | Leave terminal mode |

## Files and search

| Key | Action |
|---|---|
| `Space e` | Toggle file explorer |
| `Space E` | Reveal current file in explorer |
| `Space f f` | Find files |
| `Space f g` | Search text in project |
| `Space f w` | Search word under cursor |
| `Space f b` | Find open buffers |
| `Space f r` | Recent files |
| `Space f h` | Search help |
| `Space f k` | Search key maps |
| `Space f c` | Search commands |

## Code intelligence

| Key | Action |
|---|---|
| `gd` / `gD` | Definition / declaration |
| `grr` | References |
| `gri` | Implementations |
| `grt` | Type definition |
| `K` | Hover documentation |
| `Ctrl-k` in Insert mode | Signature help |
| `Space c a` | Code action |
| `Space c r` | Rename symbol |
| `Space c f` | Format file or selection |
| `]d` / `[d` | Next / previous diagnostic |
| `Space c d` | Diagnostic for current line |
| `Space f s` | Document symbols |
| `Space f S` | Workspace symbols |
| `Ctrl-Space` | Open completion |
| `Ctrl-y` | Accept completion |
| `Tab` / `Shift-Tab` | Navigate completion and snippets |

## Git

| Key | Action |
|---|---|
| `]h` / `[h` | Next / previous changed hunk |
| `Space h p` | Preview hunk |
| `Space h s` | Stage hunk |
| `Space h r` | Reset hunk |
| `Space h u` | Undo staged hunk |
| `Space h b` | Blame line |
| `Space h B` | Toggle inline blame |
| `Space h d` | Diff against index |
| `Space g s` | Search changed files |
| `Space g c` | Search commits |
| `Space g b` | Search branches |

## Maintenance

| Command | Action |
|---|---|
| `:Mason` | Manage language tools |
| `:LspInfo` | Inspect language servers |
| `:ConformInfo` | Inspect formatters |
| `:FormatToggle` | Toggle format-on-save globally |
| `:TSInstall <language>` | Install a Treesitter parser |
| `:PackUpdate` | Review plugin updates |
| `:checkhealth` | Diagnose the setup |
