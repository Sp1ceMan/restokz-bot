---
name: Atelier Reserve
colors:
  surface: '#fff8f4'
  surface-dim: '#dfd9d5'
  surface-bright: '#fff8f4'
  surface-container-lowest: '#ffffff'
  surface-container-low: '#f9f2ef'
  surface-container: '#f3ede9'
  surface-container-high: '#ede7e3'
  surface-container-highest: '#e7e1de'
  on-surface: '#1d1b19'
  on-surface-variant: '#434844'
  inverse-surface: '#32302e'
  inverse-on-surface: '#f6efec'
  outline: '#737873'
  outline-variant: '#c3c8c2'
  surface-tint: '#526257'
  primary: '#1a281f'
  on-primary: '#ffffff'
  primary-container: '#2f3e34'
  on-primary-container: '#98a99c'
  inverse-primary: '#bacbbd'
  secondary: '#775a00'
  on-secondary: '#ffffff'
  secondary-container: '#fed269'
  on-secondary-container: '#765900'
  tertiary: '#332021'
  on-tertiary: '#ffffff'
  tertiary-container: '#4b3536'
  on-tertiary-container: '#bc9d9e'
  error: '#ba1a1a'
  on-error: '#ffffff'
  error-container: '#ffdad6'
  on-error-container: '#93000a'
  primary-fixed: '#d5e7d9'
  primary-fixed-dim: '#bacbbd'
  on-primary-fixed: '#101f16'
  on-primary-fixed-variant: '#3b4a40'
  secondary-fixed: '#ffdf99'
  secondary-fixed-dim: '#ecc15a'
  on-secondary-fixed: '#251a00'
  on-secondary-fixed-variant: '#5a4300'
  tertiary-fixed: '#fddadb'
  tertiary-fixed-dim: '#dfbfc0'
  on-tertiary-fixed: '#291718'
  on-tertiary-fixed-variant: '#584142'
  background: '#fff8f4'
  on-background: '#1d1b19'
  surface-variant: '#e7e1de'
typography:
  headline-xl:
    fontFamily: Playfair Display
    fontSize: 36px
    fontWeight: '600'
    lineHeight: 44px
    letterSpacing: -0.02em
  headline-xl-mobile:
    fontFamily: Playfair Display
    fontSize: 28px
    fontWeight: '600'
    lineHeight: 34px
    letterSpacing: -0.01em
  headline-lg:
    fontFamily: Playfair Display
    fontSize: 26px
    fontWeight: '500'
    lineHeight: 32px
    letterSpacing: -0.01em
  headline-md:
    fontFamily: Playfair Display
    fontSize: 20px
    fontWeight: '500'
    lineHeight: 26px
    letterSpacing: 0em
  headline-sm:
    fontFamily: Playfair Display
    fontSize: 18px
    fontWeight: '500'
    lineHeight: 24px
    letterSpacing: 0em
  body-lg:
    fontFamily: Plus Jakarta Sans
    fontSize: 16px
    fontWeight: '400'
    lineHeight: 24px
    letterSpacing: -0.01em
  body-md:
    fontFamily: Plus Jakarta Sans
    fontSize: 14px
    fontWeight: '400'
    lineHeight: 20px
    letterSpacing: 0em
  body-sm:
    fontFamily: Plus Jakarta Sans
    fontSize: 12px
    fontWeight: '400'
    lineHeight: 16px
    letterSpacing: 0.01em
  label-lg:
    fontFamily: Plus Jakarta Sans
    fontSize: 14px
    fontWeight: '600'
    lineHeight: 18px
    letterSpacing: 0.02em
  label-md:
    fontFamily: Plus Jakarta Sans
    fontSize: 12px
    fontWeight: '600'
    lineHeight: 16px
    letterSpacing: 0.03em
  label-sm:
    fontFamily: Plus Jakarta Sans
    fontSize: 10px
    fontWeight: '700'
    lineHeight: 14px
    letterSpacing: 0.06em
rounded:
  sm: 0.25rem
  DEFAULT: 0.5rem
  md: 0.75rem
  lg: 1rem
  xl: 1.5rem
  full: 9999px
spacing:
  gutter: 1rem
  gutter-sm: 0.75rem
  margin: 1rem
  margin-lg: 1.5rem
  space-xs: 0.25rem
  space-sm: 0.5rem
  space-md: 0.75rem
  space-lg: 1.25rem
  space-xl: 1.75rem
---

## Brand & Style

This design system embodies the philosophy of quiet luxury, bespoke culinary hospitality, and effortless digital tactility within the Telegram Mini App environment. The visual language conveys warmth, poise, discretion, and high gastronomic culture without ostentatious decoration or aggressive interaction patterns.

### Target Audience & Emotional Intent
- **Audience:** Discerning diners, epicureans, and patrons reserving tables at boutique bistros, chef’s table residencies, and Michelin-caliber establishments.
- **Tone & Mood:** Intimate, reassuring, poised, tactile, and frictionless. The interface feels like an embossed linen menu or an invitation to a private salon.
- **Design Movement:** Warm Editorial Minimalism combined with Soft Tactile Subtlety. Generous whitespace, precise typographic cadence, whispered surface borders, and tactile micro-states replace loud dropshadows and harsh colors.

## Colors

The palette is rooted in classical culinary architecture: limestone, warm bone paper, cold-pressed olive foliage, aged gold leaf, and rich espresso.

### Role Mapping
- **Primary (`#2F3E34` - Muted Warm Olive / Forest):** Grounding architectural tone used for primary confirmation triggers, focused navigation controls, and selected interactive states.
- **Secondary (`#C29B38` - Champagne Ochre):** Applied sparingly for high-value accents: sommelier picks, chef's table indicators, status badges, and subtle focus halos.
- **Neutral / Text (`#1C1A18` - Deep Espresso Graphite):** Replaces pure digital black with a deep, organic ink tone that reduces eye strain and reinforces editorial warmth.
- **Canvas / Background (`#F9F8F6` - Soft Bone / Warm Cream):** Provides a tactile, linen-like foundation that avoids the clinical glare of `#FFFFFF`.
- **Surface Layer (`#FFFFFF` - Crisp Parchment):** Used inside cards, bottom sheets, and elevated reservation panels to create gentle layered depth over the bone canvas.
- **Divider & Border (`#E6E2DC` - Stone Calcite):** Delicately bounds cells, lists, and form inputs with razor-thin contrast.
- **Muted Subtext (`#78726A` - Warm Stone Dust):** Used for micro-copy, timestamps, ingredient notes, and disabled slots.

## Typography

The typographic hierarchy relies on the dynamic contrast between **Playfair Display** (transitional serif with refined hairlines for Russian Cyrillic editorial headings) and **Plus Jakarta Sans** (a modern, humanist grotesque engineered for effortless legibility across compact mobile screens).

### Cyrillic Editorial Rules
- Large editorial display titles (`headline-xl`, `headline-lg`) must maintain balanced optical tracking in Russian (e.g., «Столик на двоих», «Дегустационный сет»).
- High-contrast caps are preserved strictly for categorical micro-tags and badges (`label-sm`), styled with uppercase tracking (`letter-spacing: 0.06em`).
- All numeric expressions (hours, dates, guest counts, and ruble amounts) use tabular numbers (`font-variant-numeric: tabular-nums`) within Plus Jakarta Sans to prevent layout jittering during slot selection.

## Layout & Spacing

The system is optimized for Telegram WebApp viewport constraints (fixed safe area insets, variable sheet heights, dynamic viewport units).

### Layout Structure
- **Mobile-First Container:** Designed around a fluid 4-column mobile grid on devices under 480px width, expanding to a 6-column presentation for tablet and Telegram Desktop windows up to a maximum constrained canvas width of 640px.
- **Safe Area Insets:** Strict observance of Telegram top header safe area (`--tg-viewport-height`) and mobile home indicator padding at the bottom.
- **Rhythm:** Spacing tokens scale around an organic 4px/8px modular base. Dense information tiers (time slots, dietary badges) use `space-xs` and `space-sm`, while section breaks and reservation steps leverage `space-lg` and `space-xl` to maintain an airy, unhurried atmosphere.

## Elevation & Depth

Visual hierarchy is communicated through subtle tonal layering and razor-thin perimeter boundaries rather than high-contrast shadows.

### Elevation Strategy
- **Base Canvas:** `#F9F8F6` provides the root foundation.
- **Card & Sheet Elevation (Level 1):** `#FFFFFF` surfaces wrapped in a 1px border of `#E6E2DC`, supported by an ultra-diffused, ambient shadow: `box-shadow: 0 4px 20px -2px rgba(28, 26, 24, 0.04)`.
- **Floating Modals & Bottom Sheets (Level 2):** `#FFFFFF` with a 1px top outline `#E6E2DC` and a deep, soft ambient aura: `box-shadow: 0 -8px 32px 0 rgba(28, 26, 24, 0.08)`.
- **Selected Time Slots & State Overlays:** A subtle inset ring or a tinted background shift (`rgba(47, 62, 52, 0.04)`) with no artificial vertical displacement.

## Shapes

The design uses balanced rounding (`8px` base, `16px` for cards, and fully rounded pills for interactive tokens), striking an intentional equilibrium between architectural geometry and organic comfort.

- **Interactive Pills (`rounded-full`):** Reserved for time-slot buttons, party size steppers, filter chips, and primary action triggers.
- **Cards & Modular Panels (`rounded-lg` / `16px`):** Used for restaurant venue overviews, culinary course previews, and reservation summaries.
- **Bottom Drawer & Sheet Corners (`rounded-xl` / `24px` top corners):** Softens contextual drawer interactions when selecting party size, date pickers, or wine pairings.

## Components

### Buttons
- **Primary Reservation Button:** Full-width or inline rounded-pill (`height: 52px`), solid `#2F3E34` fill, crisp `#F9F8F6` typography (`label-lg`), with subtle active press compression (`transform: scale(0.98)`).
- **Secondary / Action Button:** Rounded-pill (`height: 44px`), `#FFFFFF` background, 1px `#E6E2DC` border, `#1C1A18` text. Active state adopts `background-color: #F9F8F6`.
- **Text Link Button:** Understated `#2F3E34` inline typography with a 1px offset baseline border for rules such as «Условия бронирования» or «Дресс-код».

### Time-Slot & Date Chips
- **Default State:** Pill shape, `#FFFFFF` background, 1px `#E6E2DC` outline, `#1C1A18` text (`label-md`).
- **Selected State:** Solid `#2F3E34` fill, `#FFFFFF` text, subtle elevation.
- **Unavailable / Fully Booked:** Disabled appearance with `#F9F8F6` fill, `rgba(120, 114, 106, 0.4)` text, and no border.

### Guest Stepper
- Horizontal capsule container with 1px `#E6E2DC` border, containing circular plus/minus icons and a central tabular guest counter («2 персоны», «4 персоны»).

### Cards & Sections
- **Bistro & Chef Preview Card:** `#FFFFFF` background, `16px` border-radius, hairline `#E6E2DC` border, and 16px internal padding. Image headers feature a warm desaturated grading with an optional `#C29B38` badge for Michelin Guide or Chef Residency accolades.
- **Special Occasion / Dietary Field:** Segmented card with minimal input slots, using warm `#F9F8F6` fills when idle and expanding into a clear white field upon keyboard focus.

### Inputs & Notes
- Single-line and multi-line inputs feature no heavy underlines: structured boxes with `12px` border-radius, `#FFFFFF` background, 1px `#E6E2DC` border, shifting to `#2F3E34` on focus. Placeholder text rendered in `#78726A`.

### Telegram Bottom Sticky Bar
- A persistent floating action drawer docked to the mobile safe-area baseline with frosted background treatment (`background: rgba(249, 248, 246, 0.92); backdrop-filter: blur(12px)`), housing summary metadata (e.g. «19:30 · 2 гостя») alongside the primary reservation confirmation CTA.