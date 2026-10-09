local M = {}

local function command_output(arguments)
	local result = vim.system(arguments, { text = true }):wait()
	if result.code ~= 0 then
		return nil
	end
	return vim.trim(result.stdout or "")
end

local function git_summary(cwd)
	local inside = command_output({ "git", "-C", cwd, "rev-parse", "--is-inside-work-tree" })
	if inside ~= "true" then
		return nil
	end

	local branch = command_output({ "git", "-C", cwd, "branch", "--show-current" })
	if not branch or branch == "" then
		branch = command_output({ "git", "-C", cwd, "rev-parse", "--short", "HEAD" }) or "detached"
	end

	local status = command_output({ "git", "-C", cwd, "status", "--porcelain" }) or ""
	local changes = 0
	for _ in status:gmatch("[^\r\n]+") do
		changes = changes + 1
	end

	return { branch = branch, changes = changes }
end

local function recent_files(cwd, limit)
	local project_files = {}
	local other_files = {}
	local seen = {}
	local prefix = cwd .. "/"

	for _, oldfile in ipairs(vim.v.oldfiles or {}) do
		local path = vim.fn.fnamemodify(oldfile, ":p")
		if not seen[path] and vim.fn.filereadable(path) == 1 then
			seen[path] = true
			if vim.startswith(path, prefix) then
				table.insert(project_files, path)
			else
				table.insert(other_files, path)
			end
		end
	end

	local files = {}
	for _, collection in ipairs({ project_files, other_files }) do
		for _, path in ipairs(collection) do
			table.insert(files, path)
			if #files == limit then
				return files
			end
		end
	end
	return files
end

local function fit_path(display, max_width)
	if vim.fn.strdisplaywidth(display) > max_width then
		display = vim.fn.pathshorten(display, 2)
	end
	if vim.fn.strdisplaywidth(display) > max_width then
		display = "…" .. vim.fn.strcharpart(display, vim.fn.strchars(display) - max_width + 1)
	end
	return display
end

local function display_path(path, cwd, max_width)
	local prefix = cwd .. "/"
	local display
	if vim.startswith(path, prefix) then
		display = path:sub(#prefix + 1)
	else
		display = vim.fn.fnamemodify(path, ":~")
	end

	return fit_path(display, max_width)
end

local function render()
	if vim.fn.argc() ~= 0 then
		return
	end

	local buffer = vim.api.nvim_get_current_buf()
	if vim.bo[buffer].buftype ~= "" or vim.api.nvim_buf_get_name(buffer) ~= "" then
		return
	end
	local existing = vim.api.nvim_buf_get_lines(buffer, 0, -1, false)
	if #existing > 1 or existing[1] ~= "" then
		return
	end

	local window = vim.api.nvim_get_current_win()
	local width = vim.api.nvim_win_get_width(window)
	local height = vim.api.nvim_win_get_height(window)
	local content_width = math.max(math.min(60, width - 4), 36)
	local block_padding = math.max(math.floor((width - content_width) / 2), 0)
	local cwd = vim.fn.getcwd()
	local cwd_display = fit_path(vim.fn.fnamemodify(cwd, ":~"), content_width - 4)
	local git = git_summary(cwd)
	local recent = recent_files(cwd, 5)
	local rows = {}

	local function add(text, highlight, alignment)
		table.insert(rows, { text = text or "", highlight = highlight, alignment = alignment or "left" })
	end

	local function action_row(left_key, left_label, right_key, right_label)
		if content_width < 52 then
			add(string.format("[%s] %s", left_key, left_label), "DashboardText")
			add(string.format("[%s] %s", right_key, right_label), "DashboardText")
			return
		end
		local left_width = math.floor(content_width / 2)
		local left = string.format("[%s] %s", left_key, left_label)
		add(
			left
				.. string.rep(" ", math.max(left_width - vim.fn.strdisplaywidth(left), 2))
				.. string.format("[%s] %s", right_key, right_label),
			"DashboardText"
		)
	end

	add("NVIM WORKSPACE", "DashboardTitle", "center")
	add(string.rep("─", content_width), "DashboardBorder")
	add("󰉋  " .. cwd_display, "DashboardPath")
	if git then
		local state = git.changes == 0 and "clean" or (git.changes .. (git.changes == 1 and " change" or " changes"))
		add("  " .. git.branch .. "  ·  " .. state, git.changes == 0 and "DashboardSuccess" or "DashboardWarning")
	else
		add("Not inside a Git repository", "DashboardMuted")
	end
	add()
	add("RECENT FILES", "DashboardSection")
	if #recent == 0 then
		add("No recent files yet", "DashboardMuted")
	else
		for index, path in ipairs(recent) do
			add(string.format("[%d]  %s", index, display_path(path, cwd, content_width - 5)), "DashboardText")
		end
	end
	add()
	add("QUICK ACTIONS", "DashboardSection")
	action_row("f", "Find files", "g", "Search project")
	action_row("r", "All recent files", "e", "File explorer")
	action_row("n", "New file", "c", "Edit Neovim config")
	action_row("m", "Mason tools", "k", "Key maps")
	action_row("h", "Help", "q", "Quit")
	add()
	add("Space opens the command guide  ·  Ctrl-s saves", "DashboardMuted", "center")

	local top_padding = math.max(math.floor((height - #rows) / 2) - 1, 1)
	local lines = {}
	for _ = 1, top_padding do
		table.insert(lines, "")
	end
	for _, row in ipairs(rows) do
		local inner_padding = 0
		if row.alignment == "center" then
			inner_padding = math.max(math.floor((content_width - vim.fn.strdisplaywidth(row.text)) / 2), 0)
		end
		row.padding = block_padding + inner_padding
		table.insert(lines, string.rep(" ", row.padding) .. row.text)
	end

	vim.bo[buffer].modifiable = true
	vim.api.nvim_buf_set_lines(buffer, 0, -1, false, lines)
	vim.bo[buffer].buftype = "nofile"
	vim.bo[buffer].bufhidden = "wipe"
	vim.bo[buffer].buflisted = false
	vim.bo[buffer].swapfile = false
	vim.bo[buffer].filetype = "dashboard"
	vim.bo[buffer].modifiable = false

	vim.wo[window].colorcolumn = ""
	vim.wo[window].cursorline = false
	vim.wo[window].foldcolumn = "0"
	vim.wo[window].list = false
	vim.wo[window].number = false
	vim.wo[window].relativenumber = false
	vim.wo[window].signcolumn = "no"
	vim.wo[window].statuscolumn = ""
	vim.wo[window].winbar = ""

	local namespace = vim.api.nvim_create_namespace("user_dashboard")
	for index, row in ipairs(rows) do
		local line = top_padding + index - 1
		if row.highlight then
			vim.api.nvim_buf_add_highlight(buffer, namespace, row.highlight, line, 0, -1)
		end
		local start = 1
		while true do
			local first, last = row.text:find("%[[%w%d]%]", start)
			if not first then
				break
			end
			vim.api.nvim_buf_add_highlight(
				buffer,
				namespace,
				"DashboardKey",
				line,
				row.padding + first - 1,
				row.padding + last
			)
			start = last + 1
		end
	end

	local function map(key, action, description)
		vim.keymap.set("n", key, action, { buffer = buffer, nowait = true, silent = true, desc = description })
	end

	for index, path in ipairs(recent) do
		map(tostring(index), function()
			vim.cmd.edit(vim.fn.fnameescape(path))
		end, "Open recent file " .. index)
	end
	map("f", require("fzf-lua").files, "Find files")
	map("g", require("fzf-lua").live_grep, "Search project")
	map("r", require("fzf-lua").oldfiles, "Recent files")
	map("e", "<cmd>NvimTreeToggle<cr>", "File explorer")
	map("n", "<cmd>enew<cr>", "New file")
	map("c", function()
		vim.cmd.edit(vim.fn.stdpath("config") .. "/init.lua")
	end, "Edit Neovim config")
	map("m", "<cmd>Mason<cr>", "Mason tools")
	map("k", require("fzf-lua").keymaps, "Key maps")
	map("h", require("fzf-lua").helptags, "Help")
	map("q", "<cmd>quit<cr>", "Quit")

	vim.api.nvim_win_set_cursor(window, { top_padding + 1, 0 })
	vim.cmd("setlocal cursorlineopt=number")
end

function M.setup()
	vim.api.nvim_create_autocmd("VimEnter", {
		once = true,
		callback = function()
			vim.schedule(render)
		end,
	})
end

return M
