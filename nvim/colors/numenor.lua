vim.cmd.highlight("clear")
if vim.fn.exists("syntax_on") == 1 then
	vim.cmd.syntax("reset")
end

vim.g.colors_name = "numenor"

local c = {
	base = "#08111F",
	raised = "#101C2C",
	surface = "#17283D",
	border = "#27374A",
	text = "#EEF2F6",
	muted = "#A8B4C3",
	dim = "#7D8A9B",
	gold = "#D6AE4A",
	blue = "#4C83C3",
	sea = "#79AFC7",
	urgent = "#B94747",
	success = "#5F9C83",
	none = "NONE",
}

local set = vim.api.nvim_set_hl

set(0, "Normal", { fg = c.text, bg = c.base })
set(0, "NormalNC", { fg = c.muted, bg = c.base })
set(0, "NormalFloat", { fg = c.text, bg = c.raised })
set(0, "FloatBorder", { fg = c.gold, bg = c.raised })
set(0, "FloatTitle", { fg = c.gold, bg = c.raised, bold = true })
set(0, "WinSeparator", { fg = c.border, bg = c.base })
set(0, "ColorColumn", { bg = c.raised })
set(0, "CursorLine", { bg = c.raised })
set(0, "CursorLineNr", { fg = c.gold, bg = c.raised, bold = true })
set(0, "LineNr", { fg = c.dim })
set(0, "SignColumn", { fg = c.muted, bg = c.base })
set(0, "FoldColumn", { fg = c.dim, bg = c.base })
set(0, "Folded", { fg = c.muted, bg = c.raised })
set(0, "Visual", { bg = c.surface })
set(0, "Search", { fg = c.base, bg = c.gold })
set(0, "IncSearch", { fg = c.base, bg = c.sea, bold = true })
set(0, "CurSearch", { fg = c.base, bg = c.gold, bold = true })
set(0, "MatchParen", { fg = c.gold, bg = c.surface, bold = true })
set(0, "Pmenu", { fg = c.text, bg = c.raised })
set(0, "PmenuSel", { fg = c.base, bg = c.gold, bold = true })
set(0, "PmenuSbar", { bg = c.surface })
set(0, "PmenuThumb", { bg = c.blue })
set(0, "StatusLine", { fg = c.text, bg = c.raised })
set(0, "StatusLineNC", { fg = c.dim, bg = c.raised })
set(0, "TabLine", { fg = c.muted, bg = c.raised })
set(0, "TabLineSel", { fg = c.base, bg = c.gold, bold = true })
set(0, "TabLineFill", { bg = c.base })
set(0, "Title", { fg = c.gold, bold = true })
set(0, "Directory", { fg = c.sea })
set(0, "Question", { fg = c.success })
set(0, "MoreMsg", { fg = c.success })
set(0, "WarningMsg", { fg = c.gold })
set(0, "ErrorMsg", { fg = c.urgent, bold = true })
set(0, "ModeMsg", { fg = c.gold, bold = true })
set(0, "NonText", { fg = c.border })
set(0, "Whitespace", { fg = c.border })
set(0, "SpecialKey", { fg = c.dim })

set(0, "Comment", { fg = c.dim, italic = true })
set(0, "Constant", { fg = c.sea })
set(0, "String", { fg = c.success })
set(0, "Character", { fg = c.success })
set(0, "Number", { fg = c.gold })
set(0, "Boolean", { fg = c.gold, bold = true })
set(0, "Float", { fg = c.gold })
set(0, "Identifier", { fg = c.text })
set(0, "Function", { fg = c.sea })
set(0, "Statement", { fg = c.blue, bold = true })
set(0, "Conditional", { fg = c.blue })
set(0, "Repeat", { fg = c.blue })
set(0, "Label", { fg = c.gold })
set(0, "Operator", { fg = c.muted })
set(0, "Keyword", { fg = c.blue, bold = true })
set(0, "Exception", { fg = c.urgent })
set(0, "PreProc", { fg = c.gold })
set(0, "Type", { fg = c.gold })
set(0, "StorageClass", { fg = c.gold })
set(0, "Structure", { fg = c.gold })
set(0, "Typedef", { fg = c.gold })
set(0, "Special", { fg = c.sea })
set(0, "Underlined", { fg = c.sea, underline = true })
set(0, "Todo", { fg = c.base, bg = c.gold, bold = true })
set(0, "Error", { fg = c.urgent })

set(0, "DiagnosticError", { fg = c.urgent })
set(0, "DiagnosticWarn", { fg = c.gold })
set(0, "DiagnosticInfo", { fg = c.sea })
set(0, "DiagnosticHint", { fg = c.success })
set(0, "DiagnosticOk", { fg = c.success })
set(0, "DiagnosticUnderlineError", { undercurl = true, sp = c.urgent })
set(0, "DiagnosticUnderlineWarn", { undercurl = true, sp = c.gold })
set(0, "DiagnosticUnderlineInfo", { undercurl = true, sp = c.sea })
set(0, "DiagnosticUnderlineHint", { undercurl = true, sp = c.success })

set(0, "Added", { fg = c.success })
set(0, "Changed", { fg = c.gold })
set(0, "Removed", { fg = c.urgent })
set(0, "DiffAdd", { fg = c.success, bg = "#10251F" })
set(0, "DiffChange", { fg = c.gold, bg = "#282413" })
set(0, "DiffDelete", { fg = c.urgent, bg = "#2B151B" })
set(0, "DiffText", { fg = c.text, bg = c.blue, bold = true })

set(0, "GitSignsAdd", { fg = c.success })
set(0, "GitSignsChange", { fg = c.gold })
set(0, "GitSignsDelete", { fg = c.urgent })
set(0, "NvimTreeNormal", { fg = c.text, bg = c.raised })
set(0, "NvimTreeNormalNC", { fg = c.muted, bg = c.raised })
set(0, "NvimTreeWinSeparator", { fg = c.border, bg = c.raised })
set(0, "NvimTreeRootFolder", { fg = c.gold, bold = true })
set(0, "NvimTreeFolderName", { fg = c.sea })
set(0, "NvimTreeOpenedFolderName", { fg = c.gold })
set(0, "NvimTreeGitDirty", { fg = c.gold })
set(0, "NvimTreeGitNew", { fg = c.success })
set(0, "NvimTreeGitDeleted", { fg = c.urgent })
set(0, "DevIconDefault", { fg = c.sea })
set(0, "IblIndent", { fg = c.border, nocombine = true })
set(0, "IblScope", { fg = c.gold, nocombine = true })
set(0, "WhichKey", { fg = c.gold })
set(0, "WhichKeyGroup", { fg = c.sea })
set(0, "WhichKeyDesc", { fg = c.text })
set(0, "WhichKeyNormal", { fg = c.text, bg = c.raised })
set(0, "MasonHeader", { fg = c.base, bg = c.gold, bold = true })
set(0, "MasonHighlight", { fg = c.sea })
set(0, "MasonHighlightBlock", { fg = c.base, bg = c.blue })
set(0, "DashboardTitle", { fg = c.gold, bold = true })
set(0, "DashboardBorder", { fg = c.border })
set(0, "DashboardSection", { fg = c.sea, bold = true })
set(0, "DashboardPath", { fg = c.text, bold = true })
set(0, "DashboardText", { fg = c.text })
set(0, "DashboardKey", { fg = c.gold, bold = true })
set(0, "DashboardMuted", { fg = c.dim })
set(0, "DashboardSuccess", { fg = c.success })
set(0, "DashboardWarning", { fg = c.gold })
