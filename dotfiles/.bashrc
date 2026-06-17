# ~/.bashrc: executed by bash(1) for non-login shells.
# Managed by dotfly — https://github.com/your-username/dotfly

# If not running interactively, don't do anything
case $- in
*i*) ;;
*) return ;;
esac

# History settings
HISTCONTROL=ignoreboth
shopt -s histappend
HISTSIZE=50000
HISTFILESIZE=100000
HISTTIMEFORMAT="%F %T "

# Check window size after each command
shopt -s checkwinsize

# Enable extended globbing
shopt -s globstar

# Enable programmable completion
if ! shopt -oq posix; then
  if [ -f /usr/share/bash-completion/bash_completion ]; then
    . /usr/share/bash-completion/bash_completion
  elif [ -f /etc/bash_completion ]; then
    . /etc/bash_completion
  fi
fi

# Source aliases
if [ -f ~/.bash_aliases ]; then
  . ~/.bash_aliases
fi

# PATH additions (guarded to avoid duplicates)
_pathadd() { [[ ":$PATH:" != *":$1:"* ]] && export PATH="$1:$PATH"; }
_pathadd "$HOME/.local/bin"
_pathadd "$HOME/.cargo/bin"
_pathadd "$HOME/go/bin"
unset -f _pathadd

eval "$(zoxide init bash 2>/dev/null)"
