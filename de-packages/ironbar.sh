#!/bin/bash

../templates/rust.py ironbar \
  gcc pkgconf-pkg-config \
  gtk4-devel gtk4-layer-shell-devel glib2-devel \
  pulseaudio-libs-devel libinput-devel libevdev-devel libxkbcommon-devel dbus-devel \
  luajit-devel gobject-introspection-devel \
  gdk-pixbuf2-devel
