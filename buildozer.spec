[app]
title = Multivarse Fighting
package.name = multivarsefighting
package.domain = org.capzx
source.dir = .
source.include_exts = py,png,jpg,json,ttf,wav,ogg
source.exclude_dirs = tests,preview,tools,.github,.buildozer,bin,uploads
version = 0.1.0
requirements = python3,pygame-ce,numpy
orientation = landscape
fullscreen = 1
android.api = 33
android.minapi = 24
android.ndk = 25b
android.archs = arm64-v8a, armeabi-v7a
android.allow_backup = True
android.accept_sdk_license = True
p4a.bootstrap = sdl2
android.permissions = VIBRATE

[buildozer]
log_level = 2
warn_on_root = 0
