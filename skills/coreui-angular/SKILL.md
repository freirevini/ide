---
name: coreui-angular
description: Build, review and migrate Angular apps on CoreUI 5 with Chart.js 4 (CoreUI Free/Admin template) - standalone imports and providers, icon registration, the c-chart component and its inputs, theming with data-coreui-theme and --cui-* variables, Chart.js defaults that do not read CSS, sidebar navigation pitfalls, Karma/TestBed with standalone components, and the CoreUI 4 to 5 and Chart.js 3 to 4 migration traps. Use when the project depends on @coreui/angular or @coreui/angular-chartjs, when a CoreUI component, icon, sidebar or chart misbehaves, when migrating CoreUI 4 to 5, or when the user says "CoreUI", "c-chart", "template CoreUI", "cIcon", "sidebar do CoreUI", "Chart.js no Angular".
metadata:
  version: "1.0.0"
---

# CoreUI 5 for Angular, with Chart.js 4

Covers the CoreUI layer. For general Angular use `angular-developer`, but check its advice against the pinned Angular version and test runner first: it assumes the latest Angular and Vitest.

## Step 1 - Read the pins

From `package.json`, note `@angular/core`, `@coreui/angular`, `@coreui/angular-chartjs`, `@coreui/icons-angular`, `@coreui/coreui`, `@coreui/icons`, `chart.js` and the test runner (Karma/Jasmine or Vitest/Jest).

- `@coreui/angular`, `@coreui/angular-chartjs` and `@coreui/icons-angular` are released together. Keep them on the same version. A mismatch fails at build or at runtime with injection errors.
- CoreUI 5 needs a recent Angular. CoreUI 5.5 pairs with Angular 20, which is what the 5.5.x template uses. Before upgrading either one, check the peer dependencies in the CoreUI package.
- Code from CoreUI 4 docs or demos (NgModules, `*ngIf`) does not belong in a CoreUI 5 standalone project. Rewrite it; do not paste it.

## Step 2 - Standalone wiring

- Each component imports what its template uses: `CardComponent`, `CardBodyComponent`, `RowComponent`, `ColComponent`, `ButtonDirective`, `TableDirective`, `IconDirective`, `ChartjsComponent`, and so on, from `@coreui/angular`, `@coreui/icons-angular` and `@coreui/angular-chartjs`.
- Services that the sidebar and dropdowns inject come from the module providers. In `app.config.ts`: `importProvidersFrom(SidebarModule, DropdownModule)`.
- Icons: provide `IconSetService` and register only the icons in use, by camelCase name: `iconSetService.icons = { cilTruck, cilSpeech }`. Templates use the same name: `<svg cIcon name="cilTruck">`. An icon that is not registered renders nothing and logs no error. Kebab-case `cil-truck` is the CSS/font name and does not match. When an icon is missing, check registration first.

## Step 3 - Charts (`c-chart`)

`ChartjsComponent` (selector `c-chart`) has these signal inputs: `type`, `data`, `options`, `plugins`, `height`, `width`, `redraw`, `customTooltips`, `id`, `wrapper`. Outputs: `getDatasetAtEvent`, `getElementAtEvent`, `getElementsAtEvent`, `chartRef`.

- Inputs are signals compared by reference. Mutating `data` in place does not redraw. Pass a new object on every change.
- `[redraw]="true"` destroys and recreates the chart on each change. Use it only when the type or structure changes; it costs animation and performance.
- `[customTooltips]="false"` brings back the native Chart.js tooltip. The CoreUI default is its own HTML tooltip.
- Chart.js 3 to 4 changes that break silently:
  - `scales.x.grid.drawBorder: false` becomes `scales.x.border: { display: false }`.
  - Font weight is numeric (`weight: 600`), not a string.
  - Register controllers before writing defaults: `Chart.register(...registerables)`.
- Chart.js does not read CSS variables. For light and dark themes, read the tokens with `getComputedStyle(document.documentElement)` when the theme changes. Copy them into `Chart.defaults`: `color`, `borderColor`, `font.family`, `plugins.tooltip.*`. Then call `chart.update('none')` on each chart in `Chart.instances`. Series colors in `data` must be re-read too.

## Step 4 - Theme

- CoreUI 5 switches color mode by the `data-coreui-theme="light|dark"` attribute on `<html>` and per-theme `--cui-*` variables. CoreUI ships a `ColorModeService`.
- Choose one theme owner. If the app has its own theme service, it writes `data-coreui-theme` too and maps the CoreUI text levels (`--cui-secondary-color`, `--cui-tertiary-color`, `--cui-emphasis-color`) to the app's tokens. Do not run `ColorModeService` in parallel with it.
- Override CoreUI through `--cui-*` variables on the right selector, such as `.sidebar .sidebar-nav` for navigation. Avoid hardcoded colors on CoreUI classes.
- Exports (Excel, PDF, image) are not themed. Read light tokens for them even when the screen is dark.
- Removing CoreUI branding from the UI is allowed. The MIT `LICENSE` must stay.

## Step 5 - Sidebar and navigation

- `<c-sidebar colorScheme="dark">` replaces the CoreUI 4 dark class.
- In CoreUI 5, `c-sidebar-nav-group` carries `routerLinkActive="show"`, so the component rewrites its own `show` class. Never read open or closed state from that class. Read the visible effect, such as the height of the item list, or keep your own state.
- Links with a fragment (`/page#section`) can confuse active-group detection, because the URL with fragment is compared. Use `dropdownMode="none"` and open the group yourself when the menu has section anchors.
- `ngx-perfect-scrollbar` does not compile on Angular 16+. The CoreUI 5 template uses `ngx-scrollbar`.
- After any CoreUI upgrade, smoke-test navigation by hand or with E2E: open a group, click a sub-item, use the browser back button, and check the 375 px layout. Sidebar behavior is the most common regression.

## Step 6 - Tests (Karma/Jasmine or other)

- Standalone components go in `TestBed.configureTestingModule({ imports: [MyComponent] })`, not in `declarations`.
- Standalone renders real children. For a shallow test, use `TestBed.overrideComponent(MyComponent, { set: { imports: [], schemas: [NO_ERRORS_SCHEMA] } })`.
- Charts in tests: assert on the `data` and `options` objects the component builds, not on canvas pixels.
- Keep the project's runner. Karma is deprecated upstream but still works. Moving to Vitest or Jest is a decision of its own, not a side effect of another change (`angular-jest` covers Jest).

## Migration 4 to 5, short form

1. Start from the CoreUI 5 template at the target version. Take its infrastructure: `package.json` versions, `angular.json` builder, `tsconfig*`, test config. Keep the product code.
2. Convert with the official schematics: `@angular/core:standalone` (all three modes) and `@angular/core:control-flow`.
3. Apply Steps 2 to 5: wiring, chart option changes, theme attribute, sidebar and scrollbar.
4. Compare screenshots against the old build at desktop and mobile widths, in light and dark. Expect only small chart smoothing and 1 px differences; list any difference you accept.
5. Specs change API only, never expectations. If an expectation must change, record why.

## Done means

- Build and the full test suite pass on the pinned Node version. Quote the result lines.
- Every icon used is registered; no console error on any page.
- Theme switch updates both CoreUI components and charts without reload.
- Sidebar smoke passed at desktop and 375 px.
