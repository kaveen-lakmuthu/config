local group = vim.api.nvim_create_augroup("user_config", { clear = true })

vim.api.nvim_create_autocmd("TextYankPost", {
	group = group,
	callback = function()
		vim.hl.on_yank({ higroup = "Visual", timeout = 180 })
	end,
})

vim.api.nvim_create_autocmd("BufReadPost", {
	group = group,
	callback = function(event)
		local mark = vim.api.nvim_buf_get_mark(event.buf, '"')
		local line_count = vim.api.nvim_buf_line_count(event.buf)
		if mark[1] > 0 and mark[1] <= line_count then
			pcall(vim.api.nvim_win_set_cursor, 0, mark)
		end
	end,
})

vim.api.nvim_create_autocmd("FileType", {
	group = group,
	pattern = {
		"css",
		"html",
		"javascript",
		"javascriptreact",
		"json",
		"lua",
		"markdown",
		"typescript",
		"typescriptreact",
		"yaml",
	},
	callback = function()
		vim.opt_local.shiftwidth = 2
		vim.opt_local.tabstop = 2
		vim.opt_local.softtabstop = 2
	end,
})

vim.api.nvim_create_autocmd("FileType", {
	group = group,
	callback = function(event)
		local ok, stats = pcall(vim.uv.fs_stat, vim.api.nvim_buf_get_name(event.buf))
		if ok and stats and stats.size > 1024 * 1024 then
			return
		end
		pcall(vim.treesitter.start, event.buf)
	end,
})

vim.api.nvim_create_autocmd("FileType", {
	group = group,
	pattern = { "help", "qf", "checkhealth", "man", "notify" },
	callback = function(event)
		vim.keymap.set("n", "q", "<cmd>close<cr>", { buffer = event.buf, silent = true })
	end,
})

vim.api.nvim_create_autocmd("BufEnter", {
	group = group,
	callback = function()
		vim.opt_local.formatoptions:remove({ "c", "r", "o" })
	end,
})

vim.api.nvim_create_autocmd({ "FocusGained", "TermClose", "TermLeave" }, {
	group = group,
	command = "checktime",
})
