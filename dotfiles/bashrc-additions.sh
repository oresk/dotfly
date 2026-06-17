# === dotfly additions ===

# Modern tool aliases
alias cat='batcat --pager none'
alias ls='eza'
alias fd='fdfind'
alias watch='watch --color'

# System
alias update='sudo apt update'
alias autoremove='sudo apt autoremove'

# Git branch picker
alias gbranch="git checkout \$(git for-each-ref --sort=-committerdate --format='%(refname:short)' refs/heads/ | fzf)"

# Utility
mcd() { mkdir -p "$1" && cd "$1"; }

# PATH additions (guarded)
_pathadd() { [[ ":$PATH:" != *":$1:"* ]] && export PATH="$1:$PATH"; }
_pathadd "$HOME/.local/bin"
_pathadd "$HOME/.cargo/bin"
_pathadd "$HOME/go/bin"
unset -f _pathadd

# Source .bash_aliases if it exists
if [ -f ~/.bash_aliases ]; then
  . ~/.bash_aliases
fi

# zoxide (smart cd)
eval "$(zoxide init bash 2>/dev/null)"

# fzf (if installed)
[ -f /usr/share/doc/fzf/examples/key-bindings.bash ] && source /usr/share/doc/fzf/examples/key-bindings.bash
[ -f /usr/share/doc/fzf/examples/completion.bash ] && source /usr/share/doc/fzf/examples/completion.bash
