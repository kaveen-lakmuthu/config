local border = "rounded"

vim.diagnostic.config({
	severity_sort = true,
	underline = true,
	update_in_insert = false,
	signs = {
		text = {
			[vim.diagnostic.severity.ERROR] = "●",
			[vim.diagnostic.severity.WARN] = "▲",
			[vim.diagnostic.severity.INFO] = "■",
			[vim.diagnostic.severity.HINT] = "◆",
		},
	},
	virtual_text = { spacing = 3, prefix = "●", current_line = true },
	float = { border = border, source = "if_many", header = "", prefix = "" },
})

vim.lsp.config("*", {
	root_markers = { ".git" },
})

vim.lsp.config("clangd", {
	cmd = { "clangd", "--background-index", "--clang-tidy", "--completion-style=detailed" },
})

vim.lsp.config("lua_ls", {
	settings = {
		Lua = {
			completion = { callSnippet = "Replace" },
			diagnostics = { globals = { "vim" } },
			hint = { enable = true },
			workspace = { checkThirdParty = false },
		},
	},
})

vim.lsp.config("basedpyright", {
	settings = {
		basedpyright = {
			analysis = {
				autoImportCompletions = true,
				diagnosticMode = "openFilesOnly",
				typeCheckingMode = "standard",
			},
		},
	},
})

vim.lsp.config("gopls", {
	settings = {
		gopls = {
			analyses = { unusedparams = true, shadow = true },
			gofumpt = true,
			staticcheck = true,
		},
	},
})

vim.lsp.config("rust_analyzer", {
	settings = {
		["rust-analyzer"] = {
			cargo = { allFeatures = true },
			check = { command = "clippy" },
		},
	},
})

require("mason").setup({
	ui = {
		border = border,
		icons = { package_installed = "✓", package_pending = "➜", package_uninstalled = "○" },
	},
})

local servers = {
	"bashls",
	"basedpyright",
	"cssls",
	"gopls",
	"html",
	"jsonls",
	"lua_ls",
	"rust_analyzer",
	"ts_ls",
	"yamlls",
}

require("mason-lspconfig").setup({
	ensure_installed = servers,
	automatic_enable = servers,
})

require("mason-tool-installer").setup({
	ensure_installed = vim.list_extend(vim.deepcopy(servers), {
		"stylua",
		"shfmt",
		"prettier",
		"ruff",
	}),
	auto_update = false,
	run_on_start = true,
	start_delay = 3000,
	debounce_hours = 168,
})

vim.lsp.enable("clangd")

vim.api.nvim_create_autocmd("LspAttach", {
	group = vim.api.nvim_create_augroup("user_lsp", { clear = true }),
	callback = function(event)
		local client = vim.lsp.get_client_by_id(event.data.client_id)
		local buffer = event.buf
		local fzf = require("fzf-lua")

		local function lsp_map(mode, lhs, rhs, description)
			vim.keymap.set(mode, lhs, rhs, { buffer = buffer, desc = description })
		end

		lsp_map("n", "gd", fzf.lsp_definitions, "Go to definition")
		lsp_map("n", "gD", vim.lsp.buf.declaration, "Go to declaration")
		lsp_map("n", "grr", fzf.lsp_references, "References")
		lsp_map("n", "gri", fzf.lsp_implementations, "Implementations")
		lsp_map("n", "grt", fzf.lsp_typedefs, "Type definition")
		lsp_map("n", "K", vim.lsp.buf.hover, "Hover documentation")
		lsp_map("i", "<C-k>", vim.lsp.buf.signature_help, "Signature help")
		lsp_map({ "n", "v" }, "<leader>ca", vim.lsp.buf.code_action, "Code action")
		lsp_map("n", "<leader>cr", vim.lsp.buf.rename, "Rename symbol")
		lsp_map("n", "<leader>li", "<cmd>LspInfo<cr>", "LSP information")
		lsp_map("n", "<leader>lr", "<cmd>LspRestart<cr>", "Restart LSP")

		if client and client:supports_method("textDocument/completion") then
			vim.lsp.completion.enable(true, client.id, buffer, { autotrigger = true })
		end

		if client and client:supports_method("textDocument/inlayHint") then
			vim.lsp.inlay_hint.enable(true, { bufnr = buffer })
		end

		if client and client:supports_method("textDocument/documentHighlight") then
			local highlight_group = vim.api.nvim_create_augroup("lsp_highlight_" .. buffer, { clear = true })
			vim.api.nvim_create_autocmd({ "CursorHold", "CursorHoldI" }, {
				group = highlight_group,
				buffer = buffer,
				callback = vim.lsp.buf.document_highlight,
			})
			vim.api.nvim_create_autocmd({ "CursorMoved", "InsertEnter" }, {
				group = highlight_group,
				buffer = buffer,
				callback = vim.lsp.buf.clear_references,
			})
			vim.api.nvim_create_autocmd("LspDetach", {
				group = highlight_group,
				buffer = buffer,
				once = true,
				callback = function()
					vim.lsp.buf.clear_references()
					vim.api.nvim_clear_autocmds({ group = highlight_group, buffer = buffer })
				end,
			})
		end
	end,
})
