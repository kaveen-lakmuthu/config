local plugins = {
	"https://github.com/nvim-lua/plenary.nvim",
	"https://github.com/nvim-tree/nvim-web-devicons",
	"https://github.com/nvim-tree/nvim-tree.lua",
	"https://github.com/ibhagwan/fzf-lua",
	"https://github.com/lewis6991/gitsigns.nvim",
	"https://github.com/nvim-treesitter/nvim-treesitter",
	"https://github.com/neovim/nvim-lspconfig",
	"https://github.com/mason-org/mason.nvim",
	"https://github.com/mason-org/mason-lspconfig.nvim",
	"https://github.com/WhoIsSethDaniel/mason-tool-installer.nvim",
	"https://github.com/stevearc/conform.nvim",
	"https://github.com/folke/which-key.nvim",
	"https://github.com/windwp/nvim-autopairs",
	"https://github.com/lukas-reineke/indent-blankline.nvim",
	"https://github.com/nvim-lualine/lualine.nvim",
}

vim.pack.add(plugins, { confirm = false, load = true })

vim.api.nvim_create_user_command("PackUpdate", function()
	vim.pack.update()
end, { desc = "Review and update all Neovim plugins" })

require("nvim-web-devicons").setup({
	color_icons = false,
	default = true,
})

local tree_api = require("nvim-tree.api")
local function tree_on_attach(buffer)
	tree_api.config.mappings.default_on_attach(buffer)
	local function tree_map(lhs, rhs, description)
		vim.keymap.set("n", lhs, rhs, {
			buffer = buffer,
			desc = "Tree: " .. description,
			noremap = true,
			silent = true,
			nowait = true,
		})
	end

	tree_map("l", tree_api.node.open.edit, "Open")
	tree_map("h", tree_api.node.navigate.parent_close, "Close directory")
	tree_map("v", tree_api.node.open.vertical, "Open in vertical split")
	tree_map("s", tree_api.node.open.horizontal, "Open in horizontal split")
	tree_map("?", tree_api.tree.toggle_help, "Help")
end

require("nvim-tree").setup({
	on_attach = tree_on_attach,
	disable_netrw = true,
	hijack_netrw = true,
	sync_root_with_cwd = true,
	respect_buf_cwd = true,
	update_focused_file = { enable = true, update_root = false },
	view = { width = 34, side = "left", preserve_window_proportions = true },
	renderer = {
		root_folder_label = false,
		group_empty = true,
		highlight_git = "name",
		indent_markers = { enable = true },
	},
	filters = { dotfiles = false, git_ignored = false },
	git = { enable = true, ignore = false, timeout = 400 },
	diagnostics = {
		enable = true,
		show_on_dirs = true,
		icons = { hint = "◆", info = "■", warning = "▲", error = "●" },
	},
	actions = {
		open_file = { quit_on_open = false, window_picker = { enable = false } },
	},
})

vim.keymap.set("n", "<leader>e", "<cmd>NvimTreeToggle<cr>", { desc = "Explorer" })
vim.keymap.set("n", "<leader>E", "<cmd>NvimTreeFindFile<cr>", { desc = "Reveal current file" })

local fzf = require("fzf-lua")
fzf.setup({
	winopts = {
		height = 0.86,
		width = 0.88,
		row = 0.50,
		col = 0.50,
		border = "rounded",
		preview = { border = "rounded", layout = "flex", vertical = "down:55%" },
	},
	fzf_colors = {
		fg = { "fg", "Normal" },
		bg = { "bg", "NormalFloat" },
		hl = { "fg", "Search" },
		["fg+"] = { "fg", "CursorLine" },
		["bg+"] = { "bg", "CursorLine" },
		["hl+"] = { "fg", "IncSearch" },
		info = { "fg", "DiagnosticInfo" },
		prompt = { "fg", "Function" },
		pointer = { "fg", "DiagnosticWarn" },
		marker = { "fg", "DiagnosticHint" },
		spinner = { "fg", "DiagnosticHint" },
		header = { "fg", "Comment" },
		gutter = { "bg", "NormalFloat" },
	},
	files = { formatter = "path.filename_first" },
	grep = { formatter = "path.filename_first" },
})

vim.keymap.set("n", "<leader>ff", fzf.files, { desc = "Find files" })
vim.keymap.set("n", "<leader>fg", fzf.live_grep, { desc = "Live grep" })
vim.keymap.set("n", "<leader>fw", fzf.grep_cword, { desc = "Find word under cursor" })
vim.keymap.set("n", "<leader>fb", fzf.buffers, { desc = "Buffers" })
vim.keymap.set("n", "<leader>fr", fzf.oldfiles, { desc = "Recent files" })
vim.keymap.set("n", "<leader>fh", fzf.helptags, { desc = "Help" })
vim.keymap.set("n", "<leader>fk", fzf.keymaps, { desc = "Keymaps" })
vim.keymap.set("n", "<leader>fc", fzf.commands, { desc = "Commands" })
vim.keymap.set("n", "<leader>fs", fzf.lsp_document_symbols, { desc = "Document symbols" })
vim.keymap.set("n", "<leader>fS", fzf.lsp_workspace_symbols, { desc = "Workspace symbols" })
vim.keymap.set("n", "<leader>fd", fzf.diagnostics_document, { desc = "Document diagnostics" })
vim.keymap.set("n", "<leader>fD", fzf.diagnostics_workspace, { desc = "Workspace diagnostics" })
vim.keymap.set("n", "<leader>gs", fzf.git_status, { desc = "Git status" })
vim.keymap.set("n", "<leader>gc", fzf.git_commits, { desc = "Git commits" })
vim.keymap.set("n", "<leader>gb", fzf.git_branches, { desc = "Git branches" })

require("gitsigns").setup({
	signs = {
		add = { text = "▎" },
		change = { text = "▎" },
		delete = { text = "" },
		topdelete = { text = "" },
		changedelete = { text = "▎" },
		untracked = { text = "┆" },
	},
	current_line_blame = false,
	on_attach = function(buffer)
		local gs = package.loaded.gitsigns
		local function gmap(mode, lhs, rhs, description)
			vim.keymap.set(mode, lhs, rhs, { buffer = buffer, desc = description })
		end

		gmap("n", "]h", function()
			if vim.wo.diff then
				vim.cmd.normal({ "]c", bang = true })
			else
				gs.nav_hunk("next")
			end
		end, "Next Git hunk")
		gmap("n", "[h", function()
			if vim.wo.diff then
				vim.cmd.normal({ "[c", bang = true })
			else
				gs.nav_hunk("prev")
			end
		end, "Previous Git hunk")
		gmap({ "n", "v" }, "<leader>hs", ":Gitsigns stage_hunk<cr>", "Stage hunk")
		gmap({ "n", "v" }, "<leader>hr", ":Gitsigns reset_hunk<cr>", "Reset hunk")
		gmap("n", "<leader>hS", gs.stage_buffer, "Stage buffer")
		gmap("n", "<leader>hu", gs.undo_stage_hunk, "Undo staged hunk")
		gmap("n", "<leader>hp", gs.preview_hunk, "Preview hunk")
		gmap("n", "<leader>hb", gs.blame_line, "Blame line")
		gmap("n", "<leader>hB", gs.toggle_current_line_blame, "Toggle line blame")
		gmap("n", "<leader>hd", gs.diffthis, "Diff against index")
		gmap("n", "<leader>hD", function()
			gs.diffthis("~")
		end, "Diff against previous commit")
	end,
})

require("conform").setup({
	default_format_opts = { lsp_format = "fallback" },
	formatters_by_ft = {
		c = { "clang_format" },
		cpp = { "clang_format" },
		css = { "prettier", stop_after_first = true },
		go = { "gofmt" },
		html = { "prettier", stop_after_first = true },
		javascript = { "prettier", stop_after_first = true },
		javascriptreact = { "prettier", stop_after_first = true },
		json = { "prettier", stop_after_first = true },
		lua = { "stylua" },
		markdown = { "prettier", stop_after_first = true },
		python = { "ruff_format" },
		rust = { "rustfmt" },
		sh = { "shfmt" },
		typescript = { "prettier", stop_after_first = true },
		typescriptreact = { "prettier", stop_after_first = true },
		yaml = { "prettier", stop_after_first = true },
	},
	format_on_save = function(buffer)
		if vim.g.format_on_save == false or vim.b[buffer].format_on_save == false then
			return
		end
		return { timeout_ms = 1000, lsp_format = "fallback" }
	end,
})

vim.g.format_on_save = true
vim.keymap.set({ "n", "v" }, "<leader>cf", function()
	require("conform").format({ async = true, lsp_format = "fallback" })
end, { desc = "Format file or selection" })
vim.api.nvim_create_user_command("FormatToggle", function()
	vim.g.format_on_save = not vim.g.format_on_save
	vim.notify("Format on save: " .. (vim.g.format_on_save and "on" or "off"))
end, { desc = "Toggle format on save" })

require("nvim-autopairs").setup({ check_ts = true, fast_wrap = {} })

require("ibl").setup({
	indent = { char = "│", tab_char = "│" },
	scope = { enabled = true, char = "│", show_start = false, show_end = false },
	exclude = { filetypes = { "help", "nvim-tree", "lazy", "mason", "terminal" } },
})

local palette = {
	base = "#08111F",
	raised = "#101C2C",
	surface = "#17283D",
	text = "#EEF2F6",
	muted = "#A8B4C3",
	gold = "#D6AE4A",
	blue = "#4C83C3",
	sea = "#79AFC7",
	urgent = "#B94747",
	success = "#5F9C83",
}

local lualine_theme = {
	normal = {
		a = { fg = palette.base, bg = palette.gold, gui = "bold" },
		b = { fg = palette.text, bg = palette.surface },
		c = { fg = palette.muted, bg = palette.raised },
	},
	insert = {
		a = { fg = palette.base, bg = palette.success, gui = "bold" },
		b = { fg = palette.text, bg = palette.surface },
	},
	visual = {
		a = { fg = palette.base, bg = palette.sea, gui = "bold" },
		b = { fg = palette.text, bg = palette.surface },
	},
	replace = {
		a = { fg = palette.text, bg = palette.urgent, gui = "bold" },
		b = { fg = palette.text, bg = palette.surface },
	},
	command = {
		a = { fg = palette.text, bg = palette.blue, gui = "bold" },
		b = { fg = palette.text, bg = palette.surface },
	},
	inactive = {
		a = { fg = palette.muted, bg = palette.raised },
		b = { fg = palette.muted, bg = palette.raised },
		c = { fg = palette.muted, bg = palette.raised },
	},
}

require("lualine").setup({
	options = {
		theme = lualine_theme,
		globalstatus = true,
		component_separators = { left = "│", right = "│" },
		section_separators = { left = "", right = "" },
	},
	sections = {
		lualine_a = { "mode" },
		lualine_b = { "branch", "diff", "diagnostics" },
		lualine_c = { { "filename", path = 1, symbols = { modified = " ●", readonly = " " } } },
		lualine_x = { "encoding", "fileformat", "filetype" },
		lualine_y = { "progress" },
		lualine_z = { "location" },
	},
})

local which_key = require("which-key")
which_key.setup({
	preset = "modern",
	delay = 300,
	win = { border = "rounded" },
})
which_key.add({
	{ "<leader>b", group = "Buffers" },
	{ "<leader>c", group = "Code" },
	{ "<leader>f", group = "Find" },
	{ "<leader>g", group = "Git search" },
	{ "<leader>h", group = "Git hunks" },
	{ "<leader>l", group = "LSP" },
	{ "<leader>t", group = "Terminal / toggles" },
})
