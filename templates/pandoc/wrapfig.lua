-- Sinew & Steel: wrap small inline art with LaTeX `wrapfigure`
--
-- Usage in Markdown (place the image at the START of a paragraph):
--   ![](../assets/art/ss_die_nudge.png){.wrap-right width=1.4in}
--   Your text begins here and will flow around the image.
--
-- Supported classes:
--   - wrap-right  => wrapfigure r
--   - wrap-left   => wrapfigure l
--
-- Supported attributes:
--   - width=<latex dim> (e.g. 1.2in, 3cm)
--   - wraplines=<int> (optional; hints how many lines should wrap)
--     Example: `...{.wrap-right width=1.4in wraplines=12}`
--
-- Notes:
-- - This is deliberately PDF-only; HTML/Markdown previews can ignore it.
-- - The filter only wraps images that are the *first inline* of a paragraph,
--   so authors can control placement without surprises.

local function has_class(classes, target)
  for _, c in ipairs(classes) do
    if c == target then
      return true
    end
  end
  return false
end

local function attr_get(attr, key)
  -- attr.attributes is a map in newer Pandoc versions; be defensive.
  if attr and attr.attributes then
    return attr.attributes[key]
  end
  return nil
end

local function image_src(img)
  -- Pandoc 3: Image has `src`/`title`. Older versions used `target`.
  if img and img.src and type(img.src) == "string" then
    return img.src
  end
  if img and img.target and type(img.target) == "table" then
    return img.target[1]
  end
  return ""
end

local function wrapfigure_latex(img, side)
  local width = attr_get(img.attr, "width") or "1.25in"
  local wraplines = attr_get(img.attr, "wraplines") or attr_get(img.attr, "lines")
  local src = image_src(img) or ""
  -- Keepaspectratio avoids accidental tall boxes when someone sets only width.
  local opt = ""
  if wraplines and tostring(wraplines):match("^%d+$") then
    opt = "[" .. tostring(wraplines) .. "]"
  end
  return table.concat({
    "\\begin{wrapfigure}" .. opt .. "{" .. side .. "}{" .. width .. "}",
    "\\centering",
    "\\includegraphics[width=" .. width .. ",keepaspectratio]{" .. src .. "}",
    "\\end{wrapfigure}",
  }, "\n")
end

function Para(el)
  if not el or not el.content or #el.content == 0 then
    return nil
  end

  local first = el.content[1]
  if not first or first.t ~= "Image" then
    return nil
  end

  local classes = first.attr and first.attr.classes or {}
  local side = nil
  if has_class(classes, "wrap-right") then
    side = "r"
  elseif has_class(classes, "wrap-left") then
    side = "l"
  else
    return nil
  end

  local raw = pandoc.RawBlock("latex", wrapfigure_latex(first, side))

  -- Drop the leading image and a single following space (if present).
  local new_inlines = {}
  for i = 2, #el.content do
    table.insert(new_inlines, el.content[i])
  end
  if #new_inlines > 0 and new_inlines[1].t == "Space" then
    table.remove(new_inlines, 1)
  end

  if #new_inlines == 0 then
    -- This paragraph is just the wrapped image; emit it as a block so the
    -- *next* paragraph can flow around it.
    return raw
  end

  -- Keep the image "inline" so list item bullets don't get separated from
  -- their text. `wrapfigure` is designed to be placed at the start of a
  -- paragraph.
  local raw_inline = pandoc.RawInline("latex", wrapfigure_latex(first, side))
  table.insert(new_inlines, 1, raw_inline)
  return pandoc.Para(new_inlines)
end
