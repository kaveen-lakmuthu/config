;;; $DOOMDIR/config.el -*- lexical-binding: t; -*-

;; Place your private configuration here! Remember, you do not need to run 'doom
;; sync' after modifying this file!


;; Some functionality uses this to identify you, e.g. GPG configuration, email
;; clients, file templates and snippets. It is optional.
;; (setq user-full-name "John Doe"
;;       user-mail-address "john@doe.com")

;; Doom exposes five (optional) variables for controlling fonts in Doom:
;;
;; - `doom-font' -- the primary font to use
;; - `doom-variable-pitch-font' -- a non-monospace font (where applicable)
;; - `doom-big-font' -- used for `doom-big-font-mode'; use this for
;;   presentations or streaming.
;; - `doom-symbol-font' -- for symbols
;; - `doom-serif-font' -- for the `fixed-pitch-serif' face
;;
;; See 'C-h v doom-font' for documentation and more examples of what they
;; accept. For example:
;;
(setq doom-font (font-spec :family "Hack" :size 12.5)
      doom-variable-pitch-font (font-spec :family "Noto Sans" :size 13)
      doom-big-font (font-spec :family "Hack" :size 18)
      doom-symbol-font (font-spec :family "Noto Sans Symbols 2" :size 12.5))

;; Keep Sinhala text readable without the expensive `:ui unicode' module.
;; U+0D80–U+0DFF is the dedicated Sinhala Unicode block.
(add-hook! 'after-setting-font-hook
  (set-fontset-font t '(#x0D80 . #x0DFF)
                    (font-spec :family "Noto Sans Sinhala") nil 'prepend))
;;
;; If you or Emacs can't find your font, use 'M-x describe-font' to look them
;; up, `M-x eval-region' to execute elisp code, and 'M-x doom/reload-font' to
;; refresh your font settings. If Emacs still can't find your font, it likely
;; wasn't installed correctly. Font issues are rarely Doom issues!

;; There are two ways to load a theme. Both assume the theme is installed and
;; available. You can either set `doom-theme' or manually load a theme with the
;; `load-theme' function. This is the default:
(setq doom-theme 'doom-numenor)

;; The daemon is headless while this file loads, so `window-system' is nil.
;; Put the parameter in the defaults before emacsclient creates a PGTK frame.
;; River still supplies its own focused/unfocused border around the window.
(add-to-list 'default-frame-alist '(undecorated . t))
(modify-all-frames-parameters '((undecorated . t)))

;; Keep the code overview useful without giving it a full 20-column sidebar.
(after! demap
  (setq demap-minimap-window-width 10
        demap-minimap-window-side 'right
        demap-minimap-close-kill-minimap-p nil)

  (defun +numenor-update-minimap-h (frame)
    "Show the minimap for programming files in sufficiently wide frames."
    (when (and (frame-live-p frame) (display-graphic-p frame))
      (with-selected-frame frame
        (let* ((window (frame-selected-window frame))
               (buffer (window-buffer window))
               (source (or (buffer-base-buffer buffer) buffer)))
          (with-current-buffer source
            (if (and buffer-file-name
                     (derived-mode-p 'prog-mode)
                     (>= (frame-width frame) 70))
                (demap-open nil frame)
              (demap-close nil frame)))))))

  (add-hook 'window-selection-change-functions #'+numenor-update-minimap-h)
  (add-hook 'window-buffer-change-functions #'+numenor-update-minimap-h))

(defun +numenor-start-minimap-h ()
  "Load and open the minimap when entering the first programming buffer."
  (when (display-graphic-p)
    (require 'demap)
    (+numenor-update-minimap-h (selected-frame))))

(add-hook 'prog-mode-hook #'+numenor-start-minimap-h)

;; Specify both a dark and light theme, like so and Doom will choose which one
;; to load based on your system light/dark setting:
;;
;;   (setq doom-theme '(doom-one   . doom-one-light))   ; (DARK . LIGHT)
;;
;; If you want more pro-active theme switching based on OS light/dark mode, look
;; up the `auto-dark' package.

;; This determines the style of line numbers in effect. If set to `nil', line
;; numbers are disabled. For relative line numbers, set this to `relative'.
(setq display-line-numbers-type 'relative)

;; If you use `org' and don't want your org files in the default location below,
;; change `org-directory'. It must be set before org loads!
(setq org-directory "~/org/")


;; Whenever you reconfigure a package, make sure to wrap your config in an
;; `with-eval-after-load' block, otherwise Doom's defaults may override your
;; settings. E.g.
;;
;;   (with-eval-after-load 'PACKAGE
;;     (setq x y))
;;
;; The exceptions to this rule:
;;
;;   - Setting file/directory variables (like `org-directory')
;;   - Setting variables which explicitly tell you to set them before their
;;     package is loaded (see 'C-h v VARIABLE' to look them up).
;;   - Setting doom variables (which start with 'doom-' or '+').
;;
;; Here are some additional functions/macros that will help you configure Doom.
;;
;; - `load!' for loading external *.el files relative to this one
;; - `add-load-path!' for adding directories to the `load-path', relative to
;;   this file. Emacs searches the `load-path' when you load packages with
;;   `require' or `use-package'.
;; - `map!' for binding new keys
;;
;; To get information about any of these functions/macros, move the cursor over
;; the highlighted symbol at press 'K' (non-evil users must press 'C-c c k').
;; This will open documentation for it, including demos of how they are used.
;; Alternatively, use `C-h o' to look up a symbol (functions, variables, faces,
;; etc).
;;
;; You can also try 'gd' (or 'C-c c d') to jump to their definition and see how
;; they are implemented.
