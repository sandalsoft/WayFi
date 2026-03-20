---
name: clean-web-design
description: "Guide for building clean, modern web front-ends with a professional design system featuring HSL CSS custom properties, Tailwind CSS utility classes, light/dark mode support, and shadcn/ui-inspired component architecture. Use this skill whenever building a web UI, React component, dashboard, landing page, web app, or any front-end that should look polished and professional. Also use when the user mentions wanting a 'clean' or 'modern' design, asks for dark mode support, or needs a consistent design system for their web project. This skill covers typography, color tokens, spacing, component patterns (cards, buttons, inputs, modals, navigation), layout structure, data visualization theming, loading states, and responsive design."
---

# Clean Web Design System

This skill captures a professional, minimal design aesthetic for web front-ends. The style is characterized by restrained use of color, generous whitespace, crisp typography, and seamless light/dark mode transitions — the kind of design you'd see in a well-crafted SaaS dashboard or modern productivity tool.

The system is built on three pillars:
1. **HSL CSS custom properties** as a semantic color token layer
2. **Tailwind CSS** for utility-first styling
3. **Component composition** with small, reusable UI primitives (shadcn/ui style)

Read `.claude/skills/clean-web-design/references/design-tokens.md` for the complete color token system and CSS/Tailwind setup.
Read `.claude/skills/clean-web-design/references/component-patterns.md` for copy-pasteable component code.

## Philosophy

Every pixel of border, shadow, and color should serve a purpose. The palette is intentionally narrow — mostly neutrals with a single primary accent — so the user's *content* takes center stage. Dark mode is a first-class citizen achieved by swapping CSS custom property values, not by overriding individual styles.

## Tech Stack

- **React** with TypeScript
- **Tailwind CSS** with `darkMode: ['class']`
- **Lucide React** for icons (16x16 at `h-4 w-4` default)
- **clsx + tailwind-merge** via a `cn()` utility
- **Radix UI** for accessible unstyled primitives

## Color System

Colors are HSL values in CSS custom properties on `:root` and `.dark`. Every color has a *semantic name* describing its purpose.

### Core Tokens

| Token | Purpose | Light | Dark |
|---|---|---|---|
| `--background` | Page background | white | near-black navy |
| `--foreground` | Primary text | near-black navy | near-white |
| `--primary` / `--primary-foreground` | Primary actions, emphasis | dark navy / near-white | near-white / dark navy |
| `--secondary` / `--secondary-foreground` | Secondary surfaces | pale blue-gray / dark | dark blue-gray / light |
| `--muted` / `--muted-foreground` | Muted backgrounds, subdued text | pale / medium gray | dark / lighter gray |
| `--destructive` | Error, danger | red / white | muted red / white |
| `--border` | All borders | light gray | dark blue-gray |

See `.claude/skills/clean-web-design/references/design-tokens.md` for exact HSL values.

### Status Colors

- **Success**: `text-green-600 bg-green-100` / `dark:text-green-400 dark:bg-green-900`
- **Error**: `text-red-600 bg-red-100` / `dark:text-red-400 dark:bg-red-900`
- **Warning**: `text-amber-600 bg-amber-100` / `dark:text-amber-400 dark:bg-amber-900`

## Typography

| Element | Classes | When to use |
|---|---|---|
| Page title | `text-3xl font-bold tracking-tight` | Top of each page |
| Card/section title | `text-2xl font-semibold leading-none tracking-tight` | CardTitle |
| Body text | `text-sm` | Default content size |
| Small/metadata | `text-xs text-muted-foreground` | Labels, timestamps |
| KPI / hero number | `text-2xl font-bold` | Statistics |

## Spacing & Layout

- Sidebar: fixed `w-64`, `border-r`, `bg-card`
- Main: `pl-64`, `p-8` inner
- KPI cards: `grid gap-4 md:grid-cols-2 lg:grid-cols-4`
- Between sections: `space-y-6`
- Card padding: `p-6` (standard) / `p-4` (compact)

## Components

See `.claude/skills/clean-web-design/references/component-patterns.md` for full code.

### Cards
Base: `rounded-lg border bg-card text-card-foreground shadow-sm`
Interactive: add `hover:bg-muted/50 transition-colors cursor-pointer`

### Buttons
Six variants: `default`, `destructive`, `outline`, `secondary`, `ghost`, `link`
Four sizes: `default`, `sm`, `lg`, `icon`

### Navigation
Sidebar items: `flex items-center gap-3 rounded-md px-3 py-2 text-sm font-medium transition-colors`
Active: `bg-accent text-accent-foreground`

### Loading States
Skeleton: `bg-muted animate-pulse rounded`
Spinner: `animate-spin rounded-full h-8 w-8 border-b-2 border-primary`

## Dark Mode

Toggle via `.dark` class on `<html>`. Store preference in localStorage. Use semantic token classes — they handle dark mode automatically.

## Accessibility

- Focus rings: `focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2`
- Semantic HTML: `<nav>`, `<main>`, `<aside>`, `<button>`
- Screen reader text: `<span className="sr-only">` for icon-only buttons
- Disabled: `disabled:pointer-events-none disabled:opacity-50`
