#!/bin/bash

version="6.1.0"
inet_version="4.5.4"

printf "\n=== OMNeT++ installation ===\n"

# Default installation path
install_path="/usr/src/omnetpp"

install_omnetpp() {
  echo "Installing OMNeT++..."

  echo "exit 0" > /usr/bin/xdg-desktop-menu
  chmod 744 /usr/bin/xdg-desktop-menu

  local omnetpp_download_url="https://github.com/omnetpp/omnetpp/releases/download/omnetpp-$version/omnetpp-$version-linux-x86_64.tgz"

    echo "Downloading OMNeT++ version $version... from $omnetpp_download_url"
    if ! curl -L -o "omnetpp-$version.tgz" "$omnetpp_download_url"; then
        echo "Failed to download OMNeT++. Exiting."
        return 1
    fi

    mkdir -p "$install_path"

    # Unpack OMNeT++
    echo "Unpacking OMNeT++..."
    if ! tar xfz "omnetpp-$version.tgz" -C "$install_path" --strip-components=1; then
        echo "Failed to unpack OMNeT++. Exiting."
        return 1
    fi
    rm "omnetpp-$version.tgz"

    # Set environment variables
    echo "Setting environment variables..."
    if ! source "$install_path/setenv"; then
        echo "Failed to set environment variables. Exiting."
        return 1
    fi

    echo "Adding OMNeT++ environment setup to .profile..."
    echo '[ -f "'"$install_path"'/setenv" ] && source "'"$install_path"'/setenv"' >> "$HOME/.profile"
    echo "Environment variables added to .profile."

    # Configure OMNeT++
    echo "Configuring OMNeT++..."
    cd "$install_path" || return 1

    conda install --yes --file python/requirements.txt

    if ! ./configure WITH_OSG=no WITH_QTENV=no; then
        echo "OMNeT++ configuration failed. Exiting."
        return 1
    fi

    # Build OMNeT++
    echo "Building OMNeT++..."
    if ! make -j$(($(nproc)-1)); then
        echo "OMNeT++ build failed. Exiting."
        return 1
    fi

    echo "OMNeT++ installation completed successfully."
}

# Check if the installation path exists and is not empty
if [ -d "$install_path" ] && [ "$(ls -A "$install_path")" ]; then
    echo "Installation path $install_path exists and is not empty."
    # Check Omnet++ version
    if "$install_path/bin/opp_run" -v 2>&1 | grep -q "Version: $version"; then
        echo "OMNeT++ version $version is already installed at $install_path. Continuing without installation"
        echo "Setting environment variables..."
        if ! source "$install_path/setenv"; then
            echo "Failed to set environment variables. Exiting."
            return 1
        fi
    else
        echo "$install_path exists but does not contain OMNeT++ version $version. Please chose another path or remove the existing installation."
        exit 1
    fi
else
    echo "Installation path $install_path does not exist or is empty. Continuing with installation."
   if ! install_omnetpp; then
     exit 1
  fi
fi



printf "\n=== Workspace setup ===\n"
default_workspace_path="/usr/src/workspace"

install_inet() (
  echo "Installing INET..."
  cd "$workspace_path" || exit 1

  if ! git clone https://github.com/inet-framework/inet.git --branch v${inet_version} --depth=1; then
      echo "Failed cloning INET repository. Exiting."
      exit 1
  fi

  # inet has some strange behavior with PSFP, use a commit that works
  cd "inet" || exit 1
  git checkout ${inet_version}
  opp_featuretool disable -f VoipStream
  opp_featuretool disable -f Z3GateSchedulingConfigurator

  if ! source setenv; then
      echo "Failed to set environment variables. Exiting."
      exit 1
  fi

  if ! make makefiles; then
      echo "Failed to generate makefiles. Exiting."
      exit 1
  fi

  if ! make -j$(($(nproc)-1)); then
      echo "Failed to build INET. Exiting."
      exit 1
  fi
)

create_workspace() {
    workspace_path=${workspace_path:-$default_workspace_path}

    echo "Setting up $workspace_path"
    mkdir -p "$workspace_path"
    rm -rf "$workspace_path/inet"
}

fresh_setup() {
  printf "\n=== Create a new workspace ===\n"
  create_workspace
  install_inet
}

fresh_setup



printf "\n=== Setup completed ===\n"