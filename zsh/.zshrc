# Zsh Configuration

source ~/.config/zsh/.zprofile

# Core PATH setup
export PATH=$PATH:$HOME/.scripts
export PATH=$PATH:$HOME/.local/bin
export PATH=$PATH:$HOME/.emacs.d/bin
export PATH=$PATH:$HOME/.config/emacs/bin
export PATH=$PATH:/opt/nvim-linux-x86_64/bin
export PATH=$PATH:$HOME/Android/Sdk/platform-tools
export PATH=$PATH:$HOME/Android/Sdk/emulator
export PATH=$HOME/Documents/Projects/osdev/cross/bin:$PATH
export PATH=$PATH:$HOME/go/bin

# Environment variables
export EDITOR='nvim'
export TERMINAL='foot'
export BROWSER='brave-origin'
export LANG='en_GB.UTF-8'
export LC_ALL='en_GB.UTF-8'

# Java configuration
#export JAVA_HOME=/usr/lib/jvm/java-21-openjdk-amd64

# Android SDK
export ANDROID_HOME=$HOME/Android/Sdk

# Node Version Manager
export NVM_DIR="$HOME/.nvm"
[ -s "$NVM_DIR/nvm.sh" ] && \. "$NVM_DIR/nvm.sh"

# History
ZSH_CACHE_DIR="${XDG_CACHE_HOME:-$HOME/.cache}/zsh"
mkdir -p -- "$ZSH_CACHE_DIR"
HISTSIZE=10000
SAVEHIST=10000
HISTFILE="$ZSH_CACHE_DIR/history"

setopt APPEND_HISTORY
setopt SHARE_HISTORY
setopt HIST_IGNORE_DUPS
setopt HIST_FIND_NO_DUPS
setopt HIST_REDUCE_BLANKS
setopt HIST_SAVE_NO_DUPS

# Completion
autoload -Uz compinit && compinit
zstyle ':completion:*' menu select
zstyle ':completion:*' matcher-list '' 'm:{a-zA-Z}={A-Za-Z}'
zmodload zsh/complist
_comp_options+=(globdots)

# Predictable readline-style editing. EDITOR=nvim otherwise makes Zsh select
# vi mode, which is why ordinary cursor and history keys behaved strangely.
bindkey -e
zmodload zsh/terminfo

bindkey '^[[A' up-line-or-history
bindkey '^[[B' down-line-or-history
bindkey '^[[C' forward-char
bindkey '^[[D' backward-char
bindkey '^[[H' beginning-of-line
bindkey '^[[F' end-of-line
bindkey '^[[3~' delete-char
bindkey '^[[1;5C' forward-word
bindkey '^[[1;5D' backward-word

[[ -n "${terminfo[kcuu1]}" ]] && bindkey -- "${terminfo[kcuu1]}" up-line-or-history
[[ -n "${terminfo[kcud1]}" ]] && bindkey -- "${terminfo[kcud1]}" down-line-or-history
[[ -n "${terminfo[kcuf1]}" ]] && bindkey -- "${terminfo[kcuf1]}" forward-char
[[ -n "${terminfo[kcub1]}" ]] && bindkey -- "${terminfo[kcub1]}" backward-char
[[ -n "${terminfo[khome]}" ]] && bindkey -- "${terminfo[khome]}" beginning-of-line
[[ -n "${terminfo[kend]}" ]] && bindkey -- "${terminfo[kend]}" end-of-line
[[ -n "${terminfo[kdch1]}" ]] && bindkey -- "${terminfo[kdch1]}" delete-char

# Aliases
alias v='nvim'
alias vim='nvim'
alias edit='code'
alias cat='bat'
alias ls='eza --icons=auto'
alias grep='rg'
alias ec='systemctl --user start emacs.service && emacsclient --create-frame --no-wait'
alias et='systemctl --user start emacs.service && emacsclient --tty'
alias ta='tmux new-session -A -s main'

# Prompt
PROMPT='%F{blue}%1~%f § '

# Syntax highlighting and suggestions
source /usr/share/zsh-syntax-highlighting/zsh-syntax-highlighting.zsh
source /usr/share/zsh-autosuggestions/zsh-autosuggestions.zsh

# Starship prompt
eval "$(starship init zsh)"
