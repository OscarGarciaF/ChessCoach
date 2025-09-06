# Interesting Chess

## Overview

Interesting Chess is a web application that tracks statistically anomalous win streaks by titled chess players. The application analyzes Chess.com data to identify consecutive wins with extremely low probability thresholds (≤5%, ≤1%, ≤0.1%, ≤0.01%), highlighting potentially suspicious performance patterns. The platform presents this data through an intuitive interface that mimics Chess.com's visual style, providing chess enthusiasts, coaches, and fair-play teams with a tool for identifying remarkable or questionable streaks.

## User Preferences

Preferred communication style: Simple, everyday language.

## System Architecture

### Frontend Architecture
The application is built as a static React SPA using TypeScript:
- **Framework**: React 18 with TypeScript for type safety
- **Build Tool**: Vite for fast development and optimized production builds
- **Routing**: Wouter for lightweight client-side routing
- **State Management**: Direct data imports and React state (no external state management)
- **UI Framework**: Radix UI components with shadcn/ui styling system
- **Styling**: Tailwind CSS with CSS variables for theming, designed to emulate Chess.com's visual style
- **Data Processing**: Client-side data service that processes JSON data locally

### Static Architecture
The application is fully static with no backend dependencies:
- **Data Source**: Static JSON file imported directly into the application
- **Processing**: All data transformation and analysis happens in the browser
- **Deployment**: Can be hosted on any static hosting service (GitHub Pages, Netlify, Vercel, etc.)
- **Performance**: Faster loading with no API round trips, everything cached by CDN

### Data Model
The application processes static JSON data with three main data structures:
- **Players**: Titled player information (username, title, rating, profile data)
- **Win Streaks**: Streak metadata (length, probability, tier classification, date range)
- **Games**: Individual game records within streaks (opponent data, win probability, game URLs)

### Data Service
Client-side data processing service that:
- Imports and parses the static `results.json` file
- Transforms raw data into normalized application schemas
- Provides methods matching the original API interface for easy component integration
- Handles all probability calculations and data analysis in the browser

### Development Workflow
- **Development Server**: Vite development server with hot module replacement
- **Type Safety**: Shared schema definitions using Zod validation
- **Path Aliases**: Configured for clean imports (`@/` for client, `@shared/` for shared code)
- **Build Process**: `vite build` generates optimized static files ready for deployment

### Probability Calculation System
The application implements Glicko rating system formulas to calculate win probabilities:
- Individual game win probabilities based on rating differences
- Combined streak probabilities using multiplication of individual game odds
- Tier classification system (extreme, high, moderate, low) based on probability thresholds

### Deployment Strategy
Fully static deployment optimized for performance:
- Single `vite build` command generates all static assets
- No server or database dependencies
- Can be deployed to any static hosting service
- Optimal caching and CDN distribution
- Perfect for GitHub Pages, Netlify, Vercel, or any CDN