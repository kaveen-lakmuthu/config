local map = vim.keymap.set

local function smart_window_move(direction)
	return function()
		local current = vim.api.nvim_get_current_win()
		vim.cmd("wincmd " .. direction)

		if current == vim.api.nvim_get_current_win() and vim.env.TMUX then
			local tmux_direction = {
				h = "-L",
				j = "-D",
				k = "-U",
				l = "-R",
			}
			vim.fn.system({ "tmux", "select-pane", tmux_direction[direction] })
		end
	end
end

map({ "n", "t" }, "<C-h>", smart_window_move("h"), { desc = "Move left" })
map({ "n", "t" }, "<C-j>", smart_window_move("j"), { desc = "Move down" })
map({ "n", "t" }, "<C-k>", smart_window_move("k"), { desc = "Move up" })
map({ "n", "t" }, "<C-l>", smart_window_move("l"), { desc = "Move right" })

map("n", "<C-s>", "<cmd>write<cr>", { desc = "Save file" })
map("i", "<C-s>", "<esc><cmd>write<cr>a", { desc = "Save file" })
map("n", "<esc>", "<cmd>nohlsearch<cr>", { desc = "Clear search highlight" })

map("n", "<S-h>", "<cmd>bprevious<cr>", { desc = "Previous buffer" })
map("n", "<S-l>", "<cmd>bnext<cr>", { desc = "Next buffer" })
map("n", "<leader>bd", "<cmd>bdelete<cr>", { desc = "Delete buffer" })
map("n", "<leader>bo", "<cmd>%bdelete|edit#|bdelete#<cr>", { desc = "Delete other buffers" })

map("n", "<A-j>", "<cmd>move .+1<cr>==", { desc = "Move line down" })
map("n", "<A-k>", "<cmd>move .-2<cr>==", { desc = "Move line up" })
map("v", "<A-j>", ":move '>+1<cr>gv=gv", { desc = "Move selection down" })
map("v", "<A-k>", ":move '<-2<cr>gv=gv", { desc = "Move selection up" })
map("v", "<", "<gv", { desc = "Indent left" })
map("v", ">", ">gv", { desc = "Indent right" })

map("n", "<leader>w", "<cmd>write<cr>", { desc = "Save file" })
map("n", "<leader>q", "<cmd>confirm quit<cr>", { desc = "Quit window" })
map("n", "<leader>Q", "<cmd>confirm qall<cr>", { desc = "Quit Neovim" })
map("n", "<leader>tt", "<cmd>botright 12split | terminal<cr>", { desc = "Open terminal" })
map("t", "<esc><esc>", "<C-\\><C-n>", { desc = "Leave terminal mode" })

map("n", "]d", function()
	vim.diagnostic.jump({ count = 1, float = true })
end, { desc = "Next diagnostic" })
map("n", "[d", function()
	vim.diagnostic.jump({ count = -1, float = true })
end, { desc = "Previous diagnostic" })
map("n", "<leader>cd", vim.diagnostic.open_float, { desc = "Line diagnostic" })
map("n", "<leader>cq", vim.diagnostic.setqflist, { desc = "Diagnostics to quickfix" })

map("i", "<C-Space>", function()
	vim.lsp.completion.get()
end, { desc = "Trigger completion" })

map("i", "<Tab>", function()
	if vim.snippet.active({ direction = 1 }) then
		return "<cmd>lua vim.snippet.jump(1)<cr>"
	elseif vim.fn.pumvisible() == 1 then
		return "<C-n>"
	end
	return "<Tab>"
end, { expr = true, desc = "Next completion or snippet field" })

map({ "i", "s" }, "<S-Tab>", function()
	if vim.snippet.active({ direction = -1 }) then
		return "<cmd>lua vim.snippet.jump(-1)<cr>"
	elseif vim.fn.pumvisible() == 1 then
		return "<C-p>"
	end
	return "<S-Tab>"
end, { expr = true, desc = "Previous completion or snippet field" })
