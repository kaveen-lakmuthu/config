# Graphical-session theme. The login shell sets these before starting River,
# so River, fuzzel, riverctl-spawned applications, and D-Bus services all
# inherit the same dark Qt/GTK configuration.
export QT_QPA_PLATFORM='wayland;xcb'
export QT_QPA_PLATFORMTHEME=kde
export QT_STYLE_OVERRIDE=Breeze
export GTK_THEME=Breeze-Dark

#pfetch
