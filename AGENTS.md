
# AGENTS.md — FosholCycle

## Current implementation scope — v2 integration

The planner and historical pages now use the live CycleAlgo v2 API. This section
supersedes the older mock-only and suitability-scoring examples below; retain
their design guidance, not unsupported scientific claims.

- Keep the existing same-origin `/api/cycle-algo/explore` route and request hook.
- Send the selected engine preference; never replace engine rankings with browser scores.
- Support timing, family diversity, temperature match, dry spells, and heavy rain.
- Preserve ranked/unranked entries, separate candidate/conditional groups, ties,
  units, and per-view common historical years. Unknown values are never zero.
- Show general EcoCrop matching as exploratory, not heat damage or variety validation.
- Cost, return, irrigation-dependence, and measured-soil-health controls stay disabled
  without evidence. Legume presence is descriptive, not a soil-health ranking.
- Three selected comparisons is a UI limit, not a three-path engine limit.
- Keep mock map/home previews clearly labeled and separate from live planner results.
- Never silently fall back from a failed API request to mock or featured JSON.
- Read weather coverage/cache provenance from responses. NASA is a point/grid,
  not a district average. Third-to-first repeatability remains unchecked.
- Preserve upstream `Accept-Encoding: identity`: this avoids a reproduced Node
  gzip/HTTP-1.0 parser failure. Next.js/proxy owns browser-facing compression.
- Use `npm test`, `npm run lint`, and `npm run build` for integration changes.
- Do not add a new backend, new scoring model, dependencies, or a frontend rewrite.

## 1. Project Overview

FosholCycle is a modern, data-driven agricultural decision-support web application focused on Bangladesh.

The platform helps farmers, agricultural researchers, and planners explore environmental conditions, compare crop rotation strategies, understand climate risks, and make informed farming decisions.

The project is inspired by the NASA Space Apps Challenge 2026 "Field Shift" challenge. However, NASA Space Apps Challenge branding should not appear in the main website design.

### Project Name
FosholCycle

### Tagline
Smarter Crop Rotations. Resilient Farms.

### Target Region
Bangladesh

### Main Goals
- Explore environmental and climate data by location.
- Compare different crop rotation strategies.
- Visualize rainfall, temperature, and vegetation conditions.
- Understand drought, heat, and excessive rainfall risks.
- Display uncertainty in agricultural decision-making.
- Present complex environmental data through simple visualizations.

The website should look like a real agricultural intelligence platform, not a generic dashboard.

---

## 2. Technology Stack

Use the following technologies:

- Next.js (App Router)
- JavaScript (not TypeScript)
- React
- Tailwind CSS
- shadcn/ui when necessary
- Lucide React for icons
- Leaflet / React Leaflet for maps
- Recharts for charts when needed

### Important Rules

- Use JavaScript and JSX only.
- Do not create TypeScript or TSX files.
- Use Next.js App Router.
- Prefer React Server Components by default.
- Use Client Components only when interactivity is needed.
- Add `"use client"` only where necessary.
- Use Tailwind CSS for styling.
- Use shadcn/ui components when they improve consistency or usability.
- Avoid unnecessary dependencies.
- Do not introduce additional UI frameworks.
- Keep the implementation simple and maintainable.

---

## 3. Development Scope

For the current development phase, focus on:

1. Frontend UI
2. Page layouts
3. Responsive design
4. Navigation
5. Reusable components
6. Charts and visualizations
7. Map interface
8. Mock data integration
9. UI interactions

### Backend

The project will eventually use Next.js Route Handlers for backend functionality.

Backend implementation is currently outside the scope.

Do not create API routes, database integrations, authentication systems, or external data-fetching services unless explicitly requested.

For now, use realistic mock data stored in local JavaScript files.

Keep the frontend structure easy to connect to real APIs later.

---

## 4. Design Philosophy

The website must follow a modern, professional AgriTech design system.

### Design Characteristics

- Clean and minimal
- Modern SaaS application aesthetic
- Agriculture-focused visual identity
- Professional data visualization
- Spacious layouts
- Clear typography
- Subtle borders and shadows
- Consistent spacing
- Easy-to-understand interfaces
- Accessible and responsive

Avoid:

- Excessive gradients
- Unnecessary animations
- Overly decorative elements
- Generic admin dashboard appearance
- Complicated navigation
- Unnecessary UI components
- Excessive glassmorphism

### Visual Inspiration

The interface should combine:

- Modern agricultural technology
- Earth observation platforms
- Geospatial analytics dashboards
- Clean environmental intelligence applications

The final result should feel polished, trustworthy, and production-ready.

---

## 5. Color System

Use the following colors as the primary design reference.

| Purpose | Color |
|---------|-------|
| Primary Dark Green | #163D2B |
| Agriculture Green | #3B8C5A |
| Light Green | #E8F3E8 |
| Main Background | #F7F9F5 |
| Card Background | #FFFFFF |
| Primary Text | #1E293B |
| Secondary Text | #64748B |
| Warning | #E9A23B |
| High Risk | #DC6258 |
| Water / Rainfall | #4A90C3 |

### Color Rules

- Use green for primary actions and branding.
- Use blue for rainfall and water-related information.
- Use amber for moderate risks.
- Use red for high risks.
- Use neutral backgrounds to maintain readability.
- Maintain sufficient contrast.
- Avoid introducing random colors.

Use Tailwind CSS utilities and shared theme variables for consistency.

---

## 6. Responsive Design Rules

Responsive design is mandatory.

Use the following container width system throughout the project:

```jsx
<div className="max-w-11/12 md:max-w-10/12 lg:max-w-9/12 mx-auto">
  {/* Page content */}
</div>
```

### Container Rules

- Small screens: `max-w-11/12`
- Medium screens: `md:max-w-10/12`
- Large screens: `lg:max-w-9/12`
- Always center containers using `mx-auto`.

Use this container system consistently for:

- Navigation content
- Hero sections
- Page headings
- Dashboard content
- Footer content
- General page layouts

### Full-Width Exceptions

Some components may require full width:

- Full-screen maps
- Background sections
- Large visualizations
- Edge-to-edge decorative elements

For these cases, use full-width outer sections and the standard container for inner content when appropriate.

### Responsive Behavior

Mobile:
- Single-column layouts
- Stacked cards
- Collapsible navigation
- Full-width buttons where appropriate
- Responsive charts
- Touch-friendly controls

Tablet:
- Flexible grids
- Two-column layouts where suitable
- Adjusted spacing
- Responsive map panels

Desktop:
- Multi-column layouts
- Side-by-side comparison cards
- Large interactive maps
- Spacious dashboard layouts

### Tailwind Guidelines

- Use mobile-first responsive utilities.
- Prefer `grid` and `flex`.
- Avoid unnecessary fixed widths.
- Avoid horizontal overflow.
- Use consistent gaps and padding.
- Ensure charts and maps work on smaller screens.

---

## 7. Typography

Use a clean, modern sans-serif font.

Preferred font:
- Inter

Use `next/font` when configuring fonts.

### Typography Guidelines

- Large, bold headings
- Clear heading hierarchy
- Readable body text
- Consistent font weights
- Comfortable line heights
- Muted colors for secondary information

Avoid excessive font sizes and inconsistent typography.

---

## 8. Application Pages

The application contains five main pages.

### Page 1: Landing Page

Route:
`/`

Purpose:
Introduce FosholCycle and encourage users to explore agricultural data.

Sections:

1. Navigation
2. Hero
3. Features
4. How It Works
5. Call to Action
6. Footer

#### Hero Section

Heading:
"Better Farming Starts with Better Data."

Description:
"Explore climate insights, compare crop rotations, and prepare your farm for an uncertain future."

Buttons:
- Start Exploring
- How It Works

Include an agricultural visual or dashboard preview.

#### Feature Cards

Three main features:

1. Explore Your Land
2. Compare Crop Rotations
3. Understand Climate Risk

#### How It Works

Three-step workflow:

Select a Location → Compare Rotations → Understand the Risks

Keep the landing page visually engaging without unnecessary complexity.

---

### Page 2: Explore Map

Route:
`/explore`

Purpose:
Allow users to explore environmental conditions for locations in Bangladesh.

#### Layout

Desktop:
- Large map
- Right-side information panel

Mobile:
- Map on top
- Environmental information below

#### Map Features

- Interactive Bangladesh map
- Zoom controls
- Location selection
- Location markers
- District selection
- Optional map layer controls

Use Leaflet or React Leaflet.

Remember that Leaflet requires client-side rendering in Next.js.

Use dynamic imports with SSR disabled where necessary.

#### Location Selection

Example districts:

- Rajshahi
- Rangpur
- Bogura
- Dinajpur
- Mymensingh

#### Environmental Data Cards

Show:

- Average Temperature
- Annual Rainfall
- Soil Moisture
- Vegetation Health

Additional sections:

- Rainfall trend chart
- Temperature trend chart
- Historical period selector

Use clearly labeled mock data.

Do not display unavailable metrics as real observations.

Include a button to navigate to the Rotation Planner.

---

### Page 3: Rotation Planner

Route:
`/rotation-planner`

Purpose:
Compare agricultural crop rotation strategies.

#### Main Heading

"Find the Right Rotation for Your Land"

#### Filters

- Location
- Analysis period
- Crop rotation selection

#### Rotation Comparison

Display three rotation cards.

Example:

Rotation A:
Rice → Wheat → Mung Bean

Rotation B:
Rice → Mustard → Mung Bean

Rotation C:
Rice → Potato → Mung Bean

Each rotation card should display:

- Crop sequence
- Estimated suitability score
- Relative water demand
- Climate risk level
- Strengths
- Trade-offs

Highlight the highest-scoring rotation.

#### Comparison Charts

Include:

- Suitability comparison
- Water demand comparison
- Climate risk comparison
- Trade-off summary

Use Recharts where appropriate.

#### Recommendation

Include a simple explanation of the comparison results.

Do not present estimated suitability scores as actual crop yield predictions.

---

### Page 4: Risk & Uncertainty

Route:
`/risk-uncertainty`

Purpose:
Help users understand climate variability and agricultural risks.

#### Heading

"Understand the Risk Before You Plant"

#### Risk Cards

Display:

1. Drought Risk
2. Excess Rainfall Risk
3. Heat Stress Risk

Use appropriate icons and risk indicators.

#### Charts

Include:

- Historical rainfall variability
- Temperature trends
- Rotation suitability ranges
- Risk comparison

#### Uncertainty Visualization

Display:

- Lower estimated suitability
- Average estimated suitability
- Upper estimated suitability

Use range charts or similar visualizations.

Clearly explain that these are estimated suitability ranges under historical climate conditions, not guaranteed predictions.

#### Explanation Section

Heading:
"What Does This Mean for Farmers?"

Use simple language to explain risk and uncertainty.

---

### Page 5: Data & Method

Route:
`/data-method`

Purpose:
Explain data sources, scoring methods, and limitations.

#### Heading

"Powered by Earth Data. Built for Better Decisions."

#### Data Sources

Include cards for:

NASA POWER:
- Temperature
- Precipitation
- Solar radiation
- Historical climate data

NASA SMAP:
- Soil moisture observations
- Optional future integration

NASA Vegetation Data:
- NDVI / vegetation monitoring
- Planned integration

Clearly distinguish active, mock, and planned data sources.

#### Methodology Workflow

Location Selection
→ Climate Data
→ Crop Requirements
→ Rotation Scoring
→ Risk Analysis
→ Results

#### Scoring Explanation

Explain:

- Temperature suitability
- Rainfall suitability
- Solar suitability
- Crop rotation scoring
- Historical variability

#### Limitations

Mention:

- Climate data resolution
- Historical data uncertainty
- Local soil differences
- Irrigation assumptions
- Management practices
- Estimated suitability versus actual yields

Keep the explanations readable and understandable.

---

## 9. Recommended Project Structure

Use a simple, organized structure.

```text
fosholcycle/
│
├── public/
│   ├── images/
│   └── icons/
│
├── src/
│   ├── app/
│   │   ├── layout.js
│   │   ├── page.jsx
│   │   ├── globals.css
│   │   │
│   │   ├── explore/
│   │   │   └── page.jsx
│   │   │
│   │   ├── rotation-planner/
│   │   │   └── page.jsx
│   │   │
│   │   ├── risk-uncertainty/
│   │   │   └── page.jsx
│   │   │
│   │   └── data-method/
│   │       └── page.jsx
│   │
│   ├── components/
│   │   ├── layout/
│   │   │   ├── Navbar.jsx
│   │   │   └── Footer.jsx
│   │   │
│   │   ├── common/
│   │   │   ├── SectionHeading.jsx
│   │   │   └── MetricCard.jsx
│   │   │
│   │   ├── map/
│   │   │   └── ExploreMap.jsx
│   │   │
│   │   ├── rotation/
│   │   │   └── RotationCard.jsx
│   │   │
│   │   ├── charts/
│   │   │   └── ClimateChart.jsx
│   │   │
│   │   └── ui/
│   │
│   ├── data/
│   │   ├── mockClimate.js
│   │   ├── mockRotations.js
│   │   └── districts.js
│   │
│   └── lib/
│       └── utils.js
│
├── AGENTS.md
├── package.json
└── next.config.mjs
```

This is a recommended structure, not a strict requirement.

Adapt it to the existing project structure instead of creating unnecessary folders.

---

## 10. Component Guidelines

Create reusable components when they are used in multiple places or represent meaningful UI sections.

Examples:

- Navbar
- Footer
- SectionHeading
- MetricCard
- RotationCard
- RiskCard
- ClimateChart
- LocationSelector

### Rules

- Keep components simple.
- Use clear component names.
- Avoid huge components when splitting improves readability.
- Do not over-engineer.
- Avoid unnecessary custom hooks.
- Prefer props for reusable components.
- Keep page-specific components close to their usage when practical.
- Avoid creating abstractions for one-time simple UI elements.

Use PascalCase for React component filenames.

---

## 11. shadcn/ui Guidelines

Use shadcn/ui only when it is useful.

Preferred components:

- Button
- Card
- Select
- Tabs
- Dialog
- Sheet
- Tooltip
- Skeleton
- Badge

### Rules

- Do not install every shadcn/ui component.
- Install only the components actually required.
- Customize components using Tailwind.
- Keep styling consistent with FosholCycle.
- Avoid unnecessary component wrappers.
- Prefer simple Tailwind elements for basic layouts.

---

## 12. Icons and Images

Use `lucide-react` for icons.

### Icon Rules

- Keep icon sizes consistent.
- Use icons that match their meaning.
- Avoid excessive icons.
- Use green for positive agricultural indicators.
- Use blue for rainfall and water.
- Use amber or red for risk indicators.

### Images

Use high-quality agricultural imagery where appropriate.

Preferred subjects:

- Bangladesh farmland
- Crop fields
- Aerial agricultural landscapes
- Green agricultural patterns
- Rice fields

Use Next.js `Image` component for local and appropriately configured remote images.

Avoid unrelated stock imagery.

---

## 13. Charts and Data Visualization

Use Recharts for charts when necessary.

### Chart Guidelines

- Keep charts simple and readable.
- Use consistent colors.
- Include clear labels and legends.
- Make charts responsive.
- Explain the meaning of metrics.
- Avoid unnecessary chart decorations.
- Do not use misleading scales.

Recommended chart types:

- Line charts for trends
- Bar charts for comparisons
- Horizontal bars for water demand
- Range charts for uncertainty
- Simple indicators for climate risks

Use sample data only until real data integration is requested.

Clearly label mock or illustrative data.

---

## 14. Mock Data Guidelines

During frontend development, use mock data.

Store mock data separately from UI components.

Example:

```javascript
export const climateData = {
  location: "Rajshahi",
  temperature: 28.4,
  rainfall: 1650,
  soilMoisture: null,
  ndvi: null,
  isMock: true,
};
```

### Rules

- Do not hardcode large datasets directly inside JSX.
- Keep sample data organized.
- Make data easy to replace with API responses later.
- Do not pretend mock data comes from a live NASA API.
- Use realistic values where possible.
- Show unavailable data as unavailable.
- Clearly identify estimated or illustrative metrics.

---

## 15. Navigation Guidelines

The main navigation should contain:

- Home
- Explore Map
- Rotation Planner
- Risk & Uncertainty
- Data & Method

### Requirements

- Highlight the active route.
- Use Next.js `Link` for internal navigation.
- Keep navigation consistent across pages.
- Make the mobile navigation accessible.
- Use a responsive mobile menu.
- Keep the header clean and uncluttered.

Brand name:
FosholCycle

Do not use the old project name "Field Shift" in visible branding.

---

## 16. Coding Standards

### JavaScript

- Use modern JavaScript.
- Use ES modules.
- Prefer `const` over `let` when possible.
- Use descriptive variable names.
- Keep functions short and readable.
- Avoid unnecessary complexity.
- Avoid deeply nested conditions.

### React

- Use functional components.
- Follow React hooks rules.
- Avoid unnecessary state.
- Avoid unnecessary effects.
- Avoid prop drilling when a simpler structure is possible.
- Use semantic HTML elements.

### Next.js

- Follow Next.js App Router conventions.
- Use Server Components where appropriate.
- Use Client Components for interactive features.
- Use `next/link` for navigation.
- Use `next/image` for appropriate images.
- Use `next/font` for font optimization.

### Styling

- Use Tailwind CSS.
- Avoid inline styles unless necessary.
- Avoid large custom CSS files.
- Use shared theme colors.
- Keep class names readable.
- Maintain consistent spacing and border radii.

### Comments

- Write comments only when they explain something non-obvious.
- Avoid unnecessary comments.
- Prefer self-explanatory code.

---

## 17. Accessibility

Follow basic accessibility practices.

- Use semantic HTML.
- Use descriptive button labels.
- Provide alt text for meaningful images.
- Maintain readable contrast.
- Support keyboard navigation.
- Include visible focus states.
- Make interactive elements touch-friendly.
- Do not communicate risk through color alone.

---

## 18. Performance

Keep the website lightweight.

### Rules

- Avoid unnecessary dependencies.
- Optimize images.
- Lazy-load heavy components when appropriate.
- Dynamically import Leaflet components when required.
- Avoid excessive client-side JavaScript.
- Minimize unnecessary re-renders.
- Do not load large datasets directly into UI components.
- Use responsive images.

Performance should not come at the cost of code readability.

---

## 19. Agent Working Rules

When working on FosholCycle, follow these instructions.

### Before Writing Code

1. Understand the requested task.
2. Inspect the existing project structure.
3. Check existing components and styling.
4. Reuse existing patterns when possible.
5. Avoid installing unnecessary packages.

### While Writing Code

1. Use JavaScript and JSX only.
2. Follow the existing Next.js App Router structure.
3. Use Tailwind CSS.
4. Follow the defined responsive container system.
5. Keep components reusable but simple.
6. Follow the existing color palette.
7. Maintain consistent UI across pages.
8. Use mock data when real data is unavailable.
9. Avoid unnecessary architecture changes.
10. Do not implement backend functionality unless requested.

### After Writing Code

1. Check for syntax errors.
2. Check import paths.
3. Check responsive layouts.
4. Verify navigation links.
5. Check mobile usability.
6. Remove unused imports.
7. Avoid leaving placeholder code that breaks the UI.
8. Run available lint or build checks when practical.

### Important

Do not rewrite unrelated files.

Do not introduce new frameworks without a clear reason.

Do not add complex state management libraries unless required.

Do not add authentication, databases, or API routes during the current frontend phase.

Do not replace existing working components unnecessarily.

Do not introduce TypeScript.

Do not over-engineer simple features.

---

## 20. Development Priorities

Follow this order unless a specific task requires otherwise.

### Phase 1: Foundation

- Set up the global design system.
- Configure fonts and colors.
- Build the navigation.
- Build the footer.
- Create the responsive layout system.

### Phase 2: Landing Page

- Hero section
- Feature cards
- How It Works
- Call to Action

### Phase 3: Explore Map

- Map interface
- Location selector
- Environmental metric cards
- Climate trend charts

### Phase 4: Rotation Planner

- Rotation cards
- Comparison charts
- Trade-off visualization
- Recommendation section

### Phase 5: Risk & Uncertainty

- Risk cards
- Climate risk charts
- Suitability range visualization
- Explanation sections

### Phase 6: Data & Method

- Data source cards
- Methodology workflow
- Scoring explanation
- Limitations

### Phase 7: Final Polish

- Responsive improvements
- Loading states
- Empty states
- Accessibility
- UI consistency
- Performance improvements

---

## 21. Final Project Expectations

FosholCycle should be:

- Modern
- Professional
- Responsive
- Clean
- Easy to navigate
- Agriculture-focused
- Data-driven
- Visually consistent
- Simple to maintain
- Ready for future API integration

The primary goal is to create a polished agricultural decision-support frontend that communicates meaningful information clearly.

Always prioritize:

**Simplicity → Usability → Consistency → Performance → Maintainability**

When making implementation decisions, choose the simplest reliable solution that fits the existing project.
