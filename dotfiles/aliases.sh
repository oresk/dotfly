# === dotfly aliases ===

alias cat='batcat --pager none'
alias catno='batcat --pager none --style plain'
alias ls='eza'
alias fd='fdfind'
alias update='sudo apt update'
alias autoremove='sudo apt autoremove'
alias watch='watch --color'
alias gbranch="git checkout \$(git for-each-ref --sort=-committerdate --format='%(refname:short)' refs/heads/ | fzf)"

mcd() { mkdir -p "$1" && cd "$1"; }

# A few helpful functions
extract() {
  if [ -z "$1" ]; then
    echo "Usage: extract <file>"
  else
    if [ -f "$1" ]; then
      case $1 in
        *.tar.gz) tar xvzf "$1" ;;
        *.tar.xz) tar xvJf "$1" ;;
        *.tar.bz2) tar xvjf "$1" ;;
        *.tar) tar xvf "$1" ;;
        *.zip) unzip "$1" ;;
        *.7z) 7z x "$1" ;;
        *.gz) gunzip "$1" ;;
        *.bz2) bunzip2 "$1" ;;
        *.xz) unxz "$1" ;;
        *.rar) unrar x "$1" ;;
        *) echo "extract: unknown archive: $1" ;;
      esac
    else
      echo "$1 - file does not exist"
    fi
  fi
}
