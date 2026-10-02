vim.loader.enable()

vim.g.mapleader = " "
vim.g.maplocalleader = "\\"

require("config.options")
require("config.keymaps")
require("config.autocmds")
require("config.plugins")

vim.cmd.colorscheme("numenor")

require("config.lsp")
