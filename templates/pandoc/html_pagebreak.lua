-- Sinew & Steel: HTML page-break helpers
--
-- Purpose:
-- When authoring for the LaTeX backend, it's convenient to use raw LaTeX
-- page-break commands (e.g. \clearpage). When building via HTML/CSS (WeasyPrint),
-- those commands should become HTML page-break markers instead of being dropped.
--
-- This filter converts a small set of known LaTeX-only commands into HTML
-- markers so a single Markdown source can target both backends.

local function normalize(text)
  return (text or ""):gsub("%s+", " "):gsub("^%s+", ""):gsub("%s+$", "")
end

function RawBlock(el)
  -- Pandoc may label raw TeX blocks as either "latex" or "tex" depending on
  -- input/source; accept both.
  if el.format ~= "latex" and el.format ~= "tex" then
    return nil
  end

  local t = normalize(el.text)
  local tl = t:lower()

  if tl == "\\newpage" or tl == "\\clearpage" or tl == "\\pagebreak" then
    return pandoc.RawBlock("html", '<div class="pagebreak"></div>')
  end

  -- wrapfig-specific escape hatch; in HTML/CSS we clear floats instead.
  if tl == "\\sswrapfill" then
    return pandoc.RawBlock("html", '<div style="clear: both;"></div>')
  end

  return nil
end
