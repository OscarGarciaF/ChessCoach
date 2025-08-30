# Interesting Chess

## Overview

Interesting Chess is a web application that tracks statistically anomalous win streaks by titled chess players. The application analyzes Chess.com data to identify consecutive wins with extremely low probability thresholds (≤5%, ≤1%, ≤0.1%, ≤0.01%), highlighting potentially suspicious performance patterns. The platform presents this data through an intuitive interface that mimics Chess.com's visual style, providing chess enthusiasts, coaches, and fair-play teams with a tool for identifying remarkable or questionable streaks.

## User Preferences

Preferred communication style: Simple, everyday language.

## System Architecture

### Frontend Architecture
The client is built as a React SPA using TypeScript and modern React patterns:
- **Framework**: React 18 with TypeScript for type safety
- **Build Tool**: Vite for fast development and optimized production builds
- **Routing**: Wouter for lightweight client-side routing
- **State Management**: TanStack Query for server state management and caching
- **UI Framework**: Radix UI components with shadcn/ui styling system
- **Styling**: Tailwind CSS with CSS variables for theming, designed to emulate Chess.com's visual style

### Backend Architecture
The server follows a simple Express.js REST API pattern:
- **Runtime**: Node.js with TypeScript (ESM modules)
- **Framework**: Express.js for HTTP server and routing
- **Development**: tsx for TypeScript execution in development
- **Production**: esbuild for compilation to optimized JavaScript bundles
- **Storage**: In-memory storage implementation with interface for future database integration

### Data Model
The application uses a three-entity schema optimized for chess streak analysis:
- **Players**: Stores titled player information (username, title, rating, profile data)
- **Win Streaks**: Records streak metadata (length, probability, tier classification, date range)
- **Games**: Individual game records within streaks (opponent data, win probability, game URLs)

### API Design
RESTful endpoints provide access to streak data:
- `GET /api/streaks` - Returns all interesting streaks with player data
- `GET /api/streaks/:id` - Returns detailed streak information including games
- `GET /api/analytics` - Returns aggregated analytics and distribution data

### Development Workflow
- **Database**: Drizzle ORM configured for PostgreSQL with migration support
- **Development Server**: Vite middleware integration for hot module replacement
- **Type Safety**: Shared schema definitions between client and server using Zod validation
- **Path Aliases**: Configured for clean imports (`@/` for client, `@shared/` for shared code)

### Probability Calculation System
The application implements Glicko rating system formulas to calculate win probabilities:
- Individual game win probabilities based on rating differences
- Combined streak probabilities using multiplication of individual game odds
- Tier classification system (extreme, high, moderate, low) based on probability thresholds

### Deployment Strategy
The architecture supports static deployment with CDN caching:
- Client builds to static assets for CDN distribution
- Server compiles to single JavaScript bundle for serverless deployment
- Environment-based configuration for development vs production