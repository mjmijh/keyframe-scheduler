# Keyframe Scheduler - Claude Code Context

This `.claude/` directory contains development context for Claude Code (AI coding assistant).

## 📁 Structure

```
.claude/
├── instructions.md           # High-level development instructions
├── architecture.md          # System architecture and data flow
├── rules.md                 # Code patterns and rules
├── examples/
│   ├── interpolation.py     # Keyframe interpolation implementation
│   └── blueprint-context.py # Blueprint context detection examples
└── README.md                # This file
```

## 🎯 Purpose

These files are **automatically loaded** by Claude Code and provide context for:
- Understanding the codebase architecture
- Following established code patterns
- Avoiding common bugs
- Maintaining consistency

## 📖 Quick Reference

### For New Features
1. Read `instructions.md` - Understand project principles
2. Check `architecture.md` - Understand data flow
3. Review `rules.md` - Follow code patterns
4. Reference `examples/` - See working code

### For Bug Fixes
1. Check `rules.md` → Common Bugs section
2. Review `examples/` for correct patterns
3. Test against examples in `blueprint-context.py`

### For Context Detection
See `examples/blueprint-context.py` for:
- How context tracking works
- All context source examples
- Before/After v4.0 comparison

### For Interpolation
See `examples/interpolation.py` for:
- Linear interpolation algorithm
- Midnight rollover handling
- Surrounding keyframe detection

## 🚀 Using with Claude Code

When you chat with Claude Code:
- Claude automatically knows project architecture
- Claude follows code patterns in `rules.md`
- Claude references examples when suggesting code

**Example prompts:**
```
"Add support for bezier curve interpolation instead of linear"
→ Claude will reference interpolation.py and maintain patterns

"Fix the manual override detection for Adaptive Lighting"
→ Claude will reference blueprint-context.py

"Update Blueprint to v5.0 with new feature X"
→ Claude will follow architecture.md structure
```

## 📦 What's NOT Here

❌ Secrets/API Keys (use `.env`)
❌ Generated code (use working directory)
❌ Build artifacts
❌ Very large files

## 🔄 Keeping Updated

When you make architectural changes:
1. Update relevant `.claude/*.md` files
2. Add new examples to `.claude/examples/`
3. Keep consistent with actual code

Think of `.claude/` as **living documentation** that Claude uses.

## 🤝 Integration with PICOlightnode

This Keyframe Scheduler works closely with PICOlightnode v2.0.18+:
- PICO sends `Context(id="picolightnode_restore")` on internal updates
- Blueprint v4.0 detects this context
- Manual override detection works correctly

See `examples/blueprint-context.py` for full explanation.

## 📚 Related Documentation

- Full architecture: `docs/PICO_KEYFRAME_CONCEPT.md` (in PICOlightnode repo)
- README: `README.md` (project root)
- Blueprint: `blueprints/automation/keyframe_smart_light_follower.yaml`

---

**Version**: v3.0.10
**Last Updated**: 2026-03-13
