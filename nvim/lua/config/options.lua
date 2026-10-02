local opt = vim.opt

opt.number = true
opt.relativenumber = true
opt.cursorline = true
opt.signcolumn = "yes"
opt.colorcolumn = "100"

opt.termguicolors = true
opt.showmode = false
opt.laststatus = 3
opt.cmdheight = 1

opt.mouse = "a"
opt.clipboard = "unnamedplus"
opt.confirm = true
opt.undofile = true
opt.updatetime = 250
opt.timeoutlen = 400

opt.ignorecase = true
opt.smartcase = true
opt.inccommand = "split"
opt.completeopt = { "menu", "menuone", "noselect", "popup" }

opt.expandtab = true
opt.shiftwidth = 4
opt.tabstop = 4
opt.softtabstop = 4
opt.smartindent = true

opt.splitbelow = true
opt.splitright = true
opt.scrolloff = 8
opt.sidescrolloff = 8
opt.wrap = false
opt.breakindent = true

opt.list = true
opt.listchars = {
	tab = "» ",
	trail = "·",
	nbsp = "␣",
	extends = "›",
	precedes = "‹",
}

opt.foldmethod = "expr"
opt.foldexpr = "v:lua.vim.treesitter.foldexpr()"
opt.foldlevel = 99
opt.foldlevelstart = 99
opt.foldenable = true
