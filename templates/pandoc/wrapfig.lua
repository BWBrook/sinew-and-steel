-- Sinew & Steel: wrap small inline art with LaTeX `wrapfigure`
--
-- Usage in Markdown (place the image at the START of a paragraph):
--   ![](../assets/art/ss_die_nudge.png){.wrap-right width=1.4in}
--   Your text begins here and will flow around the image.
--
-- Supported classes:
--   - wrap-right  => wrapfigure r (inside the text block)
--   - wrap-left   => wrapfigure l (inside the text block)
--
-- Compatibility / deprecation:
--   - margin-right / margin-left used to emit `\marginpar`, but margin figures
--     look bad in bound books and can get clipped. Treat them as aliases for
--     wrap-right / wrap-left so no output ever goes into the page margin.
--
-- Supported attributes:
--   - width=<latex dim> (e.g. 1.2in, 3cm)
--   - wraplines=<int> (optional; hints how many lines should wrap)
--     Example: `...{.wrap-right width=1.4in wraplines=12}`
--   - trim="<l> <b> <r> <t>" (optional; LaTeX includegraphics trim, e.g. "0.1in 0.1in 0.1in 0.1in")
--
-- Notes:
-- - This is deliberately PDF-only; HTML/Markdown previews can ignore it.
-- - Wrapfig can misbehave if wrapping spills into “structured” blocks
--   (lists, tables, blockquotes, headings, raw LaTeX). To keep authoring
--   ergonomic, we automatically insert `\SSwrapfill` before such blocks when
--   a wrapfigure was recently started, so the layout can’t cascade.

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

local function includegraphics_opts(img, width)
  local trim = attr_get(img.attr, "trim")
  local opts = "width=" .. width .. ",keepaspectratio"
  if trim and type(trim) == "string" and trim:gsub("%s+", "") ~= "" then
    opts = opts .. ",trim=" .. trim .. ",clip"
  end
  return opts
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
    "\\includegraphics[" .. includegraphics_opts(img, width) .. "]{" .. src .. "}",
    "\\end{wrapfigure}",
  }, "\n")
end

local function wrap_kind_for_image(img)
  local classes = img.attr and img.attr.classes or {}
  if has_class(classes, "wrap-right") or has_class(classes, "margin-right") then
    return "r"
  end
  if has_class(classes, "wrap-left") or has_class(classes, "margin-left") then
    return "l"
  end
  return nil
end

local function transform_para_like(block)
  if not block or not block.content or #block.content == 0 then
    return { block }, false
  end

  local first = block.content[1]
  if not first or first.t ~= "Image" then
    return { block }, false
  end

  local side = wrap_kind_for_image(first)
  if not side then
    return { block }, false
  end

  local latex = wrapfigure_latex(first, side)
  local raw_block = pandoc.RawBlock("latex", latex)

  -- Drop the leading image and a single following space (if present).
  local new_inlines = {}
  for i = 2, #block.content do
    table.insert(new_inlines, block.content[i])
  end
  if #new_inlines > 0 and new_inlines[1].t == "Space" then
    table.remove(new_inlines, 1)
  end

  if #new_inlines == 0 then
    -- This paragraph is just the wrapped image; emit it as a block so the
    -- *next* paragraph can flow around it.
    return { raw_block }, true
  end

  -- Keep the wrapfigure at the start of the paragraph so text wraps
  -- correctly. This also avoids the list bullet being separated from the
  -- first line of text.
  local raw_inline = pandoc.RawInline("latex", latex)
  table.insert(new_inlines, 1, raw_inline)

  if block.t == "Plain" then
    return { pandoc.Plain(new_inlines) }, true
  end
  return { pandoc.Para(new_inlines) }, true
end

local function is_wrap_unsafe_block(block)
  if not block or not block.t then
    return false
  end

  -- Let headings flow around art. This is especially useful for “portrait then
  -- character name” patterns in skins, and avoids trying to clear before a
  -- wrap has actually started.
  if block.t == "Header" or block.t == "HorizontalRule" then
    return false
  end

  -- Safe: plain paragraphs can wrap naturally.
  if block.t == "Para" or block.t == "Plain" then
    return false
  end

  -- Everything else can conflict with wrapfig’s internal parshape/margin
  -- bookkeeping, especially lists/tables/blockquotes/headers.
  return true
end

local function process_blocks(blocks)
  local out = pandoc.List:new()
  local wrap_active = false

  for _, block in ipairs(blocks) do
    -- If a wrapfigure might still be active, prevent it from spilling into
    -- structured blocks.
    if wrap_active and is_wrap_unsafe_block(block) then
      out:insert(pandoc.RawBlock("latex", "\\SSwrapfill"))
      wrap_active = false
    end

    if block.t == "Para" or block.t == "Plain" then
      local transformed, started = transform_para_like(block)
      for _, b in ipairs(transformed) do
        out:insert(b)
      end
      if started then
        wrap_active = true
      end
    elseif block.t == "BlockQuote" then
      local inner = process_blocks(block.content)
      out:insert(pandoc.BlockQuote(inner))
      -- Don’t allow a wrap started inside a quote to leak outward.
      wrap_active = false
    elseif block.t == "Div" then
      local inner = process_blocks(block.content)
      out:insert(pandoc.Div(inner, block.attr))
      wrap_active = false
    elseif block.t == "BulletList" then
      local items = {}
      for _, item in ipairs(block.content) do
        table.insert(items, process_blocks(item))
      end
      out:insert(pandoc.BulletList(items))
      wrap_active = false
    elseif block.t == "OrderedList" then
      local new_items = {}
      for _, item in ipairs(block.content) do
        table.insert(new_items, process_blocks(item))
      end
      out:insert(pandoc.OrderedList(new_items, block.listAttributes))
      wrap_active = false
    else
      out:insert(block)
    end
  end

  -- If wrapping is still active at the end of a block list, clear it so it
  -- can’t cascade into whatever comes next (or the next page).
  if wrap_active then
    out:insert(pandoc.RawBlock("latex", "\\SSwrapfill"))
  end

  return out
end

function Pandoc(doc)
  doc.blocks = process_blocks(doc.blocks)
  return doc
end
