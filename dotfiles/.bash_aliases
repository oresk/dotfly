# ~/.bash_aliases — managed by dotfly

# Modern tool aliases (install these tools first!)
alias cat='batcat --pager none'
alias ls='eza'
alias fd='fdfind'

# System
alias update='sudo apt update'
alias upgrade='sudo apt update && sudo apt upgrade'
alias autoremove='sudo apt autoremove'
alias watch='watch --color'

# Git
alias gbranch="git checkout \$(git for-each-ref --sort=-committerdate --format='%(refname:short)' refs/heads/ | fzf)"

# Utility
mcd() {
  mkdir -p "$1" && cd "$1"
}
