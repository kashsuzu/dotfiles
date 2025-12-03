-- init.lua or a separate lua config file

-- Set leader key
vim.g.mapleader = " "  -- optional, just a common setup
vim.opt.mouse = ""
-- Clipboard configuration for Wayland using wl-copy/wl-paste
vim.opt.clipboard = "unnamed"

-- Explicitly define clipboard provider functions
vim.g.clipboard = {
    name = "wl-clipboard",
    copy = {
        ["+"] = "wl-copy",
        ["*"] = "wl-copy",
    },
    paste = {
        ["+"] = "wl-paste --no-newline",
        ["*"] = "wl-paste --no-newline",
    },
    cache_enabled = 0,
}
vim.keymap.set('n', '<C-d>', '<C-d>zz')
vim.keymap.set('n', '<C-u>', '<C-u>zz')
vim.keymap.set('i','jk', '<Esc>')

-- Optional: some basic settings
vim.opt.number = true             -- show line numbers
vim.opt.relativenumber = true     -- relative line numbers
vim.opt.expandtab = true          -- convert tabs to spaces
vim.opt.smartindent = true

