# Spec: Color Theme (Issue #13)

## Overview

Implement a professional color palette and consistent typography across the todo-app UI to establish a cohesive visual identity and improve usability.

## Background

**Issue**: [#13 Color Theme](../../issues/13)
**Labels**: `tier-1`, `ui-ux`, `sprint-1`, `demo9`
**Assignee**: demo9-labworksdev

The application currently lacks a defined visual design system. This spec establishes the foundational design tokens — colors, typography, and component styles — that will be applied consistently across the UI.

---

## Goals

- Define a cohesive color palette using CSS custom properties (design tokens)
- Establish consistent heading and body font styles
- Style all interactive elements: buttons, inputs, and links
- Create clear visual hierarchy to guide user attention

## Non-Goals

- Dark mode support (can be a follow-up)
- Animations or transitions (separate concern)
- Responsive/mobile-specific layout changes

---

## Design Tokens

### Color Palette

| Token | Value | Usage |
|-------|-------|-------|
| `--color-primary` | `#2563EB` | Primary actions, links |
| `--color-primary-hover` | `#1D4ED8` | Hover state for primary |
| `--color-secondary` | `#64748B` | Secondary text, borders |
| `--color-success` | `#16A34A` | Completed todos, confirmations |
| `--color-danger` | `#DC2626` | Delete actions, errors |
| `--color-warning` | `#D97706` | Warnings, pending states |
| `--color-bg` | `#F8FAFC` | Page background |
| `--color-surface` | `#FFFFFF` | Card/panel backgrounds |
| `--color-border` | `#E2E8F0` | Borders, dividers |
| `--color-text` | `#1E293B` | Primary body text |
| `--color-text-muted` | `#94A3B8` | Placeholder, disabled text |

### Typography

| Token | Value | Usage |
|-------|-------|-------|
| `--font-family` | `Inter, system-ui, sans-serif` | All text |
| `--font-size-sm` | `0.875rem` (14px) | Labels, captions |
| `--font-size-base` | `1rem` (16px) | Body text |
| `--font-size-lg` | `1.125rem` (18px) | Subheadings |
| `--font-size-xl` | `1.25rem` (20px) | Section headings |
| `--font-size-2xl` | `1.5rem` (24px) | Page title |
| `--font-weight-normal` | `400` | Body text |
| `--font-weight-medium` | `500` | Labels, nav items |
| `--font-weight-bold` | `700` | Headings |
| `--line-height-body` | `1.6` | Body text |
| `--line-height-heading` | `1.2` | Headings |

---

## Component Styles

### Buttons

| Variant | Background | Text | Border | Use Case |
|---------|------------|------|--------|----------|
| Primary | `--color-primary` | white | none | Add todo, Save |
| Secondary | transparent | `--color-secondary` | `--color-border` | Cancel, Back |
| Danger | `--color-danger` | white | none | Delete todo |

All buttons: `border-radius: 6px`, `padding: 0.5rem 1rem`, `font-weight: medium`.

### Inputs

- Border: `1px solid --color-border`
- Border radius: `6px`
- Padding: `0.5rem 0.75rem`
- Focus ring: `2px solid --color-primary` with `outline-offset: 2px`
- Placeholder text color: `--color-text-muted`

### Links

- Default: `--color-primary`, no underline
- Hover: `--color-primary-hover`, underline
- Visited: `--color-secondary`

### Visual Hierarchy

1. **Page title** — `2xl`, `bold`, `--color-text`
2. **Section headings** — `xl`, `bold`, `--color-text`
3. **Item titles** — `base`, `medium`, `--color-text`
4. **Supporting text** — `sm`, `normal`, `--color-text-muted`

---

## Implementation Plan

1. **Create `static/css/tokens.css`** — define all CSS custom properties under `:root`
2. **Create `static/css/base.css`** — apply tokens to HTML elements (`body`, `h1`–`h4`, `a`, `input`, `button`)
3. **Create `static/css/components.css`** — button variants, input states, links
4. **Import stylesheets** in the base HTML template
5. **Audit existing templates** — replace any hardcoded colors/fonts with token references

## Acceptance Criteria

- [ ] All color and typography values sourced from CSS custom properties
- [ ] Page title, section headings, body text, and muted text are visually distinct
- [ ] Primary, secondary, and danger button variants are implemented and used consistently
- [ ] Input fields have visible focus states meeting WCAG 2.1 AA contrast requirements
- [ ] Links are distinguishable from body text without relying solely on color
- [ ] No hardcoded hex values or font names outside of `tokens.css`

---

## References

- [ARCHITECTURE.md](../ARCHITECTURE.md) — project structure
- [WCAG 2.1 AA contrast guidelines](https://www.w3.org/TR/WCAG21/#contrast-minimum)
