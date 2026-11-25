#!/bin/bash
# Make a retained Heimdall release available by name for the current Bash user.
set -euo pipefail
umask 077

root=$(cd "$(dirname "$0")/.." && pwd)
if [ "$#" -gt 1 ]; then
  printf 'Usage: bash scripts/install-cli.sh [path-to-heimdall-launcher]\n' >&2
  exit 2
fi

launcher=${1:-"$root/bin/heimdall"}
launcher_directory=$(cd "$(dirname "$launcher")" && pwd -P)
launcher="$launcher_directory/$(basename "$launcher")"
if [ ! -f "$launcher" ] || [ ! -x "$launcher" ]; then
  printf 'Heimdall launcher must be an executable file: %s\n' "$launcher" >&2
  exit 1
fi

command_directory="$HOME/.local/bin"
destination="$command_directory/heimdall"
marker='# Installed by Heimdall install-cli.sh'
if [ "$launcher" = "$destination" ] || [ "$launcher" -ef "$destination" ]; then
  printf 'Choose the Heimdall release launcher instead of %s\n' "$destination" >&2
  exit 1
fi
if [ -L "$destination" ] ||
   { [ -e "$destination" ] && { [ ! -f "$destination" ] || ! grep -Fxq "$marker" "$destination"; }; }; then
  printf 'A command already exists at %s. Move it before installing Heimdall.\n' "$destination" >&2
  exit 1
fi

mkdir -p "$command_directory"
temporary=$(mktemp "$command_directory/.heimdall.XXXXXXXX")
trap 'rm -f -- "$temporary"' EXIT
printf '#!/bin/bash\n%s\nexec %q "$@"\n' "$marker" "$launcher" > "$temporary"
chmod 755 "$temporary"
mv -f -- "$temporary" "$destination"

# Bash reads the first available login profile and reads .bashrc for new
# interactive non-login shells, such as a terminal opened in the desktop.
login_profile="$HOME/.profile"
for candidate in "$HOME/.bash_profile" "$HOME/.bash_login"; do
  if [ -r "$candidate" ]; then
    login_profile="$candidate"
    break
  fi
done
for startup_file in "$login_profile" "$HOME/.bashrc"; do
  if ! grep -Fxq '# Heimdall command directory' "$startup_file" 2>/dev/null; then
    cat >> "$startup_file" <<'PATH_SETUP'

# Heimdall command directory
case ":$PATH:" in
  *":$HOME/.local/bin:"*) ;;
  *) export PATH="$HOME/.local/bin:$PATH" ;;
esac
PATH_SETUP
  fi
done

printf '%s\n' 'Open a new Bash terminal and run heimdall --help or heimdall --console.'
